import asyncio
from grapheteria import Node, WorkflowEngine

class Agent(Node):
    async def prepare(self, shared, request_input):
        await asyncio.sleep(1)
        input = "I am agent 1"
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
        workflow = WorkflowEngine(workflow_id="workflow", run_id="20250413_131736_187", resume_from=2)
        await workflow.step(input_data={"Agent_9b": "Hello"})

    asyncio.run(main())