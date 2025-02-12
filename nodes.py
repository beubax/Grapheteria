from machine import SyncNode, AsyncNode, WorkflowEngine
import asyncio
import json
import random

class AgentNode(AsyncNode):
    async def prepare(self, _):
        message = "Hello from agent node!"
        return message
        
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"] = execution_result
    
    
class TestNode(SyncNode):
    def prepare(self, _):
        return "Hello from test node!"
        
    def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"] = execution_result
    
# Example usage:
async def main():
    
    workflow = WorkflowEngine.from_json("workflow.json")
    
    # Continue execution
    while True:
        has_more_steps = await workflow.step()
        print(workflow.execution_state)
        if not has_more_steps:
            break
    
    print("\nFinal state:", workflow.execution_state.to_dict())  # Changed to access execution_state directly

if __name__ == "__main__":
    asyncio.run(main())