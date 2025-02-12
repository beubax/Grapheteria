from dataclasses import dataclass
from typing import Dict,Any,Optional,List,Type,ClassVar,Set
from enum import Enum,auto
from datetime import datetime
import asyncio,copy,time,inspect
from abc import ABC,abstractmethod

class WorkflowStatus(Enum): NOT_STARTED,RUNNING,COMPLETED,FAILED=auto(),auto(),auto(),auto()
class NodeStatus(str,Enum): ACTIVE,COMPLETED,FAILED="active","completed","failed"

@dataclass
class ExecutionState:
    shared:Dict[str,Any];current_node_ids:Set[str];node_statuses:Dict[str,NodeStatus];history:List[Dict[str,Any]];workflow_status:WorkflowStatus
    def to_dict(self): return {'shared':self.shared,'current_node_ids':list(self.current_node_ids),'node_statuses':{k:v.value for k,v in self.node_statuses.items()},'history':self.history,'workflow_status':self.workflow_status.name}
    @classmethod
    def from_dict(cls,d): return cls(shared=d['shared'],current_node_ids=set(d['current_node_ids']),node_statuses={k:NodeStatus(v) for k,v in d['node_statuses'].items()},history=d['history'],workflow_status=WorkflowStatus[d['workflow_status']])

class BaseNode(ABC):
    registry:ClassVar[Dict[str,Type['BaseNode']]] = {}
    def __init__(self,id=None,config=None,max_retries=1,wait=0): self.id,self.type,self.config,self.transitions,self.max_retries,self.wait,self.cur_retry=id or f"{self.__class__.__name__}_{id(self)}",self.__class__.__name__,config or {},{},max_retries,wait,0
    def __init_subclass__(cls,**k): super().__init_subclass__(**k);cls.registry.update({cls.__name__:cls}) if not inspect.isabstract(cls) else None
    def get_next_node_ids(self,s): return {t.to_id for t in self.transitions.values() if t.should_transition(s)}
    def add_transition(self, transition): self.transitions[transition.to_id] = transition
    @classmethod
    def from_dict(cls,d): return cls.registry[d['class']](id=d['id'],config=d.get('config',{})) if d['class'] in cls.registry else ValueError(f"Unknown node: {d['class']}")

class SyncNode(BaseNode):
    def run(self,s):
        s.node_statuses[self.id]=NodeStatus.ACTIVE;p=self.prepare(s)
        for self.cur_retry in range(self.max_retries):
            try: return self.cleanup(s,p,e:=self.execute(p)) if not s.node_statuses.update({self.id:NodeStatus.COMPLETED}) else None
            except Exception as e:
                if self.cur_retry==self.max_retries-1: s.node_statuses[self.id]=NodeStatus.FAILED;return self.exec_fallback(p,e)
                time.sleep(self.wait) if self.wait>0 else None
    def prepare(self,s): return None
    @abstractmethod
    def execute(self,p): pass
    def cleanup(self,s,p,e): return e
    def exec_fallback(self,p,e): raise e

class AsyncNode(BaseNode):
    async def run(self,s):
        s.node_statuses[self.id]=NodeStatus.ACTIVE;p=await self.prepare(s)
        for self.cur_retry in range(self.max_retries):
            try: return await self.cleanup(s,p,e:=await self.execute(p)) if not s.node_statuses.update({self.id:NodeStatus.COMPLETED}) else None
            except Exception as e:
                if self.cur_retry==self.max_retries-1: s.node_statuses[self.id]=NodeStatus.FAILED;return await self.exec_fallback(p,e)
                await asyncio.sleep(self.wait) if self.wait>0 else None
    async def prepare(self,s): return None
    @abstractmethod
    async def execute(self,p): pass
    async def cleanup(self,s,p,e): return e
    async def exec_fallback(self,p,e): raise e

class Transition:
    def __init__(self,from_id,to_id,condition="True"): self.from_id,self.to_id,self.condition=from_id,to_id,condition
    def should_transition(self,s): return eval(self.condition,{"__builtins__":{}},{"shared":s.shared,"True":True,"False":False,"None":None})
    @classmethod
    def from_dict(cls,d): return cls(from_id=d['from'],to_id=d['to'],condition=d.get('condition','True'))

class WorkflowEngine:
    def __init__(self,nodes_dict,start_node_id,workflow_id,workflow_name=None,initial_shared_state=None,max_parallel_nodes=10): self.nodes,self.start_node_id,self.workflow_id,self.workflow_name,self.max_parallel_nodes,self.execution_state=nodes_dict,start_node_id,workflow_id,workflow_name or workflow_id,max_parallel_nodes,ExecutionState(shared=initial_shared_state or {},current_node_ids={start_node_id},node_statuses={},history=[],workflow_status=WorkflowStatus.NOT_STARTED)
    def save_state(self): return {'workflow_id':self.workflow_id,'workflow_name':self.workflow_name,'execution_state':self.execution_state.to_dict()}
    @classmethod
    def load_state(cls,nodes_dict,d): e=cls(nodes_dict=nodes_dict,start_node_id=list(nodes_dict)[0],workflow_id=d['workflow_id'],workflow_name=d['workflow_name']);e.execution_state=ExecutionState.from_dict(d['execution_state']);return e
    async def execute_node(self,nid): n=copy.copy(self.nodes[nid]);r=await n.run(self.execution_state) if isinstance(n,AsyncNode) else n.run(self.execution_state);next_ids=n.get_next_node_ids(self.execution_state);[self.execution_state.history.append({'timestamp':datetime.now().isoformat(),'from_node':nid,'to_node':i}) for i in next_ids];return next_ids
    async def step(self):
        if self.execution_state.workflow_status not in {WorkflowStatus.NOT_STARTED,WorkflowStatus.RUNNING}: return False
        self.execution_state.workflow_status=WorkflowStatus.RUNNING
        if not self.execution_state.current_node_ids: self.execution_state.workflow_status=WorkflowStatus.COMPLETED;return False
        try: c=list(self.execution_state.current_node_ids)[:self.max_parallel_nodes];n=await asyncio.gather(*(self.execute_node(i) for i in c));self.execution_state.current_node_ids-=set(c);[self.execution_state.current_node_ids.update(s) for s in n];[self.execution_state.node_statuses.update({i:NodeStatus.PENDING}) for i in self.execution_state.current_node_ids if i not in self.execution_state.node_statuses];return bool(self.execution_state.current_node_ids)
        except Exception as e: self.execution_state.workflow_status=WorkflowStatus.FAILED;raise
    @classmethod
    def from_dict(cls,d): n={i['id']:BaseNode.from_dict(i) for i in d['nodes']};[n[e['from']].transitions.update({e['to']:Transition.from_dict(e)}) for e in d['edges']];return cls(nodes_dict=n,start_node_id=d['start'],workflow_id=d['workflow_id'],workflow_name=d.get('workflow_name'),initial_shared_state=d.get('initial_state'))