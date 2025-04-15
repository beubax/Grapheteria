import asyncio
from grapheteria import Node, WorkflowEngine

class Agent(Node):
    async def prepare(self, shared, request_input):
        input = await request_input()
        return input
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["result"] = prepared_result

class Agent2(Node):
    async def prepare(self, shared, request_input):
        input = await request_input()
        return input
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["result"] = prepared_result
    
    
if __name__ == "__main__":
    async def main():
        workflow = WorkflowEngine(workflow_id="workflow", nodes=[Agent(), Agent2()])
        await workflow.run()


    asyncio.run(main())