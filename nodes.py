import asyncio
from machine import Node, WorkflowEngine

class AgentNode(Node):
    async def prepare(self, state, request_input):
        message = await request_input()
        return message
        
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append(execution_result)

class TestNode(Node):
    def prepare(self, _, request_input):
        return request_input
    
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        res = await prepared_result()
        return res
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append(execution_result)
        return "Tejas"
    
class FlowNode(Node):
    def prepare(self, _, request_input):
        return request_input
    
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        res = await prepared_result()
        return res
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append(execution_result)
        return "Trisha"
   

if __name__ == "__main__":
    workflow = WorkflowEngine(workflow_id="workflows.workflow")
    asyncio.run(workflow.step())