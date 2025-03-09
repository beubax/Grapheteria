from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, List, Type, ClassVar, Set
from enum import Enum, auto
from datetime import datetime
import asyncio, copy, json, time, inspect, os, logging, glob
from abc import ABC, abstractmethod
from uuid import uuid4

_NODE_REGISTRY: Dict[str, Type['Node']] = {}

class WorkflowStatus(Enum): NOT_STARTED,RUNNING,COMPLETED,FAILED,WAITING_FOR_INPUT=auto(),auto(),auto(),auto(),auto()
class NodeStatus(str,Enum): PENDING,ACTIVE,WAITING_FOR_INPUT,COMPLETED,FAILED="pending","active","waiting_for_input","completed","failed"

@dataclass
class ExecutionState:
    shared:Dict[str,Any];current_node_ids:Set[str];node_statuses:Dict[str,NodeStatus];history:List[Dict[str,Any]];workflow_status:WorkflowStatus
    awaiting_inputs:Optional[Dict[str,Dict[str,Any]]]=None;input_data:Optional[Dict[str,Any]]=None;previous_node_ids:Set[str]=field(default_factory=set)
    
    def to_dict(self): return {'shared':self.shared,'current_node_ids':list(self.current_node_ids),'node_statuses':{k:v.value for k,v in self.node_statuses.items()},
        'history':self.history,'workflow_status':self.workflow_status.name,'input_data':self.input_data,
        'awaiting_inputs':{k:v for k,v in self.awaiting_inputs.items()} if self.awaiting_inputs else None,'previous_node_ids':list(self.previous_node_ids)}
    
    @classmethod
    def from_dict(cls,d): return cls(shared=d['shared'],current_node_ids=set(d['current_node_ids']),node_statuses={k:NodeStatus(v) for k,v in d['node_statuses'].items()},
        history=d['history'],workflow_status=WorkflowStatus[d['workflow_status']],input_data=d.get('input_data'),
        awaiting_inputs={k:v for k,v in d.get('awaiting_inputs',{}).items()} if d.get('awaiting_inputs') else None,previous_node_ids=set(d.get('previous_node_ids',[])))

class InputRequest:
    def __init__(self,node_id,request_type,prompt=None,options=None): self.node_id,self.request_type,self.prompt,self.options=node_id,request_type,prompt,options

class Node(ABC):
    def __init__(self,id=None,config=None,max_retries=1,wait=0): 
        self.id,self.type,self.config,self.transitions,self.max_retries,self.wait,self.cur_retry=id or f"{self.__class__.__name__}_{id(self)}",self.__class__.__name__,config or {},{},max_retries,wait,0
    
    def __init_subclass__(cls,**k): super().__init_subclass__(**k);_NODE_REGISTRY.update({cls.__name__:cls}) if not inspect.isabstract(cls) else None
    
    @classmethod
    def get_registry(cls): return _NODE_REGISTRY
    @classmethod
    def clear_registry(cls): _NODE_REGISTRY.clear()
    
    def get_next_node_ids(self,s): return {t.to_id for t in self.transitions.values() if t.should_transition(s)}
    def add_transition(self,t): self.transitions[t.to_id]=t
    
    @classmethod
    def from_dict(cls,d): 
        node_type=cls.get_registry().get(d['class'])
        return node_type(id=d['id'],config=d.get('config',{})) if node_type else ValueError(f"Unknown node type: {d['class']}. Available: {', '.join(sorted(cls.get_registry().keys()))}")
    
    async def run(self,s,request_input):
        s.node_statuses[self.id]=NodeStatus.ACTIVE;p=await(p_result:=self.prepare(s.shared,request_input)) if inspect.isawaitable(p_result:=self.prepare(s.shared,request_input)) else p_result
        for self.cur_retry in range(self.max_retries):
            try: 
                r=self.execute(p);e=await r if inspect.isawaitable(r) else r
                s.node_statuses[self.id]=NodeStatus.COMPLETED;c=self.cleanup(s.shared,p,e);return await c if inspect.isawaitable(c) else c
            except Exception as e:
                if self.cur_retry==self.max_retries-1: 
                    s.node_statuses[self.id]=NodeStatus.FAILED;f=self.exec_fallback(p,e);return await f if inspect.isawaitable(f) else f
                await asyncio.sleep(self.wait) if self.wait>0 else None
        return None
    
    def prepare(self,shared,request_input): return None
    @abstractmethod
    def execute(self,p): pass
    def cleanup(self,shared,p,e): return e
    def exec_fallback(self,p,e): raise e

class Transition:
    def __init__(self,from_id,to_id,condition="True"): self.from_id,self.to_id,self.condition=from_id,to_id,condition
    def should_transition(self,s): 
        try: return eval(self.condition,{"__builtins__":{}},{"shared":s.shared,"True":True,"False":False,"None":None})
        except Exception as e: print(f"Error in condition '{self.condition}': {str(e)}");return False
    @classmethod
    def from_dict(cls,d): return cls(from_id=d['from'],to_id=d['to'],condition=d.get('condition','True'))

class WorkflowEngine:
    def __init__(self,json_path=None,nodes_dict=None,start_node_id=None,workflow_id=None,workflow_name=None,
                initial_shared_state=None,max_parallel_nodes=10,run_id=None,auto_resume=False,resume_timestamp=None):
        if json_path:
            with open(json_path,"r") as f: data=json.load(f)
            nodes_dict={n['id']:Node.from_dict(n) for n in data['nodes']}
            [nodes_dict[t.from_id].add_transition(t) for t in [Transition.from_dict(e) for e in data['edges']]]
            start_node_id,workflow_id,workflow_name,initial_shared_state,max_parallel_nodes=data['start'],data['workflow_id'],data.get('workflow_name'),data.get('initial_state',{}),data.get('max_parallel_nodes',max_parallel_nodes)
        
        if not nodes_dict or not start_node_id or not workflow_id: raise ValueError("Must provide json_path or (nodes_dict, start_node_id, and workflow_id)")
        
        self.nodes,self.start_node_id,self.workflow_id,self.workflow_name,self.max_parallel_nodes=nodes_dict,start_node_id,workflow_id,workflow_name or workflow_id,max_parallel_nodes
        self.run_id=run_id or f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        self.log_dir=f"logs/{self.workflow_id}/{self.run_id}";os.makedirs(self.log_dir,exist_ok=True)
        
        if resume_timestamp: self._resume_from_timestamp(resume_timestamp)
        elif auto_resume: self._resume_latest()
        else: self.execution_state=ExecutionState(shared=initial_shared_state or {},current_node_ids={start_node_id},node_statuses={},history=[],workflow_status=WorkflowStatus.NOT_STARTED)
        
        self._input_futures={}
    
    def _resume_latest(self):
        state_files=sorted([f for f in os.listdir(self.log_dir) if f.startswith("state_")],key=lambda x:os.path.getmtime(os.path.join(self.log_dir,x)),reverse=True)
        if not state_files: raise FileNotFoundError(f"No state files in {self.log_dir}")
        self.load_state(os.path.join(self.log_dir,state_files[0]))
    
    def _resume_from_timestamp(self,ts):
        exact_path=os.path.join(self.log_dir,f"state_{ts}.json")
        if os.path.exists(exact_path): self.load_state(exact_path);self._purge_newer_states(ts);return
        
        try:
            state_files=sorted([f for f in os.listdir(self.log_dir) if f.startswith(f"state_{ts}") and f.endswith(".json")],reverse=True)
            if not state_files: raise FileNotFoundError()
            self.load_state(os.path.join(self.log_dir,state_files[0]));self._purge_newer_states(state_files[0].split("_")[1].split(".")[0])
        except (FileNotFoundError,IndexError):
            available=sorted([f.split("_")[1].split(".")[0] for f in os.listdir(self.log_dir) if f.startswith("state_") and f.endswith(".json")])[:10]
            raise FileNotFoundError(f"No state file matching '{ts}'. Available: {', '.join(available)}{' and more...' if len(available)==10 else ''}")
    
    def _purge_newer_states(self,ts):
        files_to_remove=[os.path.join(self.log_dir,f) for f in os.listdir(self.log_dir) 
                         if f.startswith("state_") and f.endswith(".json") and f.split("_",1)[1].split(".",1)[0]>ts]
        [os.remove(f) for f in files_to_remove]
    
    def save_state(self):
        if not self.execution_state: return
        ts=datetime.now().strftime("%Y%m%d_%H%M%S_%f");counter=0
        while True:
            suffix=f"_{counter}" if counter>0 else "";filename=f"state_{ts}{suffix}.json";filepath=os.path.join(self.log_dir,filename)
            if not os.path.exists(filepath): break
            counter+=1;
            if counter>100: raise RuntimeError("Failed to generate unique state filename")
        
        state_data=self.execution_state.to_dict();state_data['metadata']={'workflow_id':self.workflow_id,'workflow_name':self.workflow_name,'run_id':self.run_id,'save_time':ts}
        temp_path=f"{filepath}.tmp"
        with open(temp_path,'w') as f: json.dump(state_data,f)
        os.rename(temp_path,filepath)
    
    async def execute_node(self,node_id):
        node=copy.copy(self.nodes[node_id])
        
        if isinstance(node,Node):
            async def request_input(prompt=None,options=None,input_type="text",request_id=None):
                actual_request_id=request_id if request_id else node_id
                
                if hasattr(self.execution_state,'input_data') and self.execution_state.input_data:
                    node_input=self.execution_state.input_data.get(actual_request_id)
                    if node_input is not None: del self.execution_state.input_data[actual_request_id];return node_input
                
                self.execution_state.node_statuses[node_id]=NodeStatus.WAITING_FOR_INPUT
                
                if not hasattr(self.execution_state,'awaiting_inputs'): self.execution_state.awaiting_inputs={}
                
                self.execution_state.awaiting_inputs[actual_request_id]={'node_id':node_id,'request_id':actual_request_id,'prompt':prompt,'options':options,'input_type':input_type}
                self.execution_state.workflow_status=WorkflowStatus.WAITING_FOR_INPUT
                
                if hasattr(self.execution_state,'save_callback') and callable(self.execution_state.save_callback): self.execution_state.save_callback()
                
                future=asyncio.Future();self._input_futures[actual_request_id]=future
                return await future
            
            _=await node.run(self.execution_state,request_input)
        
        next_node_ids=node.get_next_node_ids(self.execution_state)
        
        for next_node_id in next_node_ids:
            self.execution_state.history.append({'timestamp':datetime.now().isoformat(),'from_node':node_id,'to_node':next_node_id})
        
        return next_node_ids
    
    async def step(self,input_data=None):
        if self.execution_state.workflow_status not in {WorkflowStatus.NOT_STARTED,WorkflowStatus.RUNNING,WorkflowStatus.WAITING_FOR_INPUT}: return False
        
        resume_tasks=[]
        
        if input_data and hasattr(self.execution_state,'awaiting_inputs'):
            if not hasattr(self.execution_state,'input_data'): self.execution_state.input_data={}
            
            for request_id,message in input_data.items():
                if request_id in self.execution_state.awaiting_inputs:
                    waiting_info=self.execution_state.awaiting_inputs[request_id];node_id=waiting_info['node_id']
                    self.execution_state.input_data[request_id]=message
                    
                    if request_id in self._input_futures:
                        future=self._input_futures[request_id]
                        if not future.done():
                            async def resume_node(node_id,future,message):
                                try:
                                    future.set_result(message);await asyncio.sleep(0)
                                    node=self.nodes[node_id];next_node_ids=node.get_next_node_ids(self.execution_state)
                                    
                                    if next_node_ids:
                                        self.execution_state.current_node_ids|=next_node_ids
                                        timestamp=datetime.now().isoformat()
                                        for next_id in next_node_ids:
                                            self.execution_state.history.append({'timestamp':timestamp,'from_node':node_id,'to_node':next_id})
                                            if next_id not in self.execution_state.node_statuses:
                                                self.execution_state.node_statuses[next_id]=NodeStatus.PENDING
                                except Exception as e:
                                    self.execution_state.node_statuses[node_id]=NodeStatus.FAILED
                                    logging.error(f"Error resuming node {node_id}: {str(e)}")
                            
                            resume_tasks.append(asyncio.create_task(resume_node(node_id,future,message)))
                        
                        del self._input_futures[request_id]
                    else: self.execution_state.current_node_ids.add(node_id)
                    
                    del self.execution_state.awaiting_inputs[request_id]
            
            waiting_nodes=set()
            for info in getattr(self.execution_state,'awaiting_inputs',{}).values(): waiting_nodes.add(info['node_id'])
            
            for node_id in list(self.execution_state.node_statuses.keys()):
                if node_id not in waiting_nodes and self.execution_state.node_statuses[node_id]==NodeStatus.WAITING_FOR_INPUT:
                    self.execution_state.node_statuses[node_id]=NodeStatus.ACTIVE
            
            if not waiting_nodes: self.execution_state.workflow_status=WorkflowStatus.RUNNING
        
        if self.execution_state.workflow_status==WorkflowStatus.WAITING_FOR_INPUT and not input_data:
            awaiting_node_ids=set(getattr(self.execution_state,'awaiting_inputs',{}).keys())
            executable_nodes=self.execution_state.current_node_ids-awaiting_node_ids
            
            if not executable_nodes: return True
            
            current_nodes=list(executable_nodes)[:self.max_parallel_nodes]
        else: current_nodes=list(self.execution_state.current_node_ids)[:self.max_parallel_nodes]
        
        self.execution_state.save_callback=self.save_state
        
        try:
            if resume_tasks: await asyncio.gather(*resume_tasks)
            
            self.execution_state.previous_node_ids=set(current_nodes)
            
            if current_nodes:
                execution_tasks=[self.execute_node(node_id) for node_id in current_nodes]
                next_node_sets=await asyncio.gather(*execution_tasks)
                
                self.execution_state.current_node_ids-=set(current_nodes)
                for next_nodes in next_node_sets: self.execution_state.current_node_ids|=next_nodes
                
                for node_id in self.execution_state.current_node_ids:
                    if node_id not in self.execution_state.node_statuses:
                        self.execution_state.node_statuses[node_id]=NodeStatus.PENDING
            
            if not self.execution_state.current_node_ids and not getattr(self.execution_state,'awaiting_inputs',{}):
                self.execution_state.workflow_status=WorkflowStatus.COMPLETED
            
            self.save_state()
            
            return self.execution_state.workflow_status in {WorkflowStatus.RUNNING,WorkflowStatus.WAITING_FOR_INPUT}
        
        except Exception as e:
            self.execution_state.workflow_status=WorkflowStatus.FAILED;self.save_state();raise
    
    def load_state(self,filepath):
        with open(filepath,'r') as f: state_data=json.load(f)
        
        self.execution_state=ExecutionState.from_dict(state_data)
        
        required_nodes=set()
        
        for entry in self.execution_state.history:
            if 'from_node' in entry: required_nodes.add(entry['from_node'])
            if 'to_node' in entry: required_nodes.add(entry['to_node'])
        
        if getattr(self.execution_state,'awaiting_inputs',None):
            for info in self.execution_state.awaiting_inputs.values():
                if 'node_id' in info: required_nodes.add(info['node_id'])
        
        required_nodes.update(self.execution_state.previous_node_ids)
        
        available_nodes=set(self.nodes.keys())
        missing_nodes=required_nodes-available_nodes
        
        if missing_nodes:
            raise ValueError(f"Cannot load state: {len(missing_nodes)} required nodes missing. First few: {', '.join(sorted(missing_nodes)[:3])}. Create a new run ID to continue.")
        
        self.execution_state.current_node_ids=set()
        
        for node_id in self.execution_state.previous_node_ids:
            if node_id in self.nodes:
                node=self.nodes[node_id]
                next_nodes=node.get_next_node_ids(self.execution_state)
                self.execution_state.current_node_ids.update(next_nodes)
        
        waiting_exists=bool(getattr(self.execution_state,'awaiting_inputs',None))
        
        if not self.execution_state.current_node_ids and not waiting_exists:
            self.execution_state.workflow_status=WorkflowStatus.COMPLETED
        elif waiting_exists:
            self.execution_state.workflow_status=WorkflowStatus.WAITING_FOR_INPUT
        else:
            self.execution_state.workflow_status=WorkflowStatus.RUNNING
    
    def get_available_timestamps(self):
        return [f.split('_')[1] for f in os.listdir(self.log_dir) if f.startswith("state_")]
    
    def get_waiting_nodes(self):
        if not hasattr(self.execution_state,'awaiting_inputs'): return []
        
        return [{'request_id':request_id,'node_id':info['node_id'],'prompt':info['prompt'],'options':info['options'],'input_type':info['input_type']}
                for request_id,info in self.execution_state.awaiting_inputs.items()]