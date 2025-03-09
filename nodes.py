from machine import Node, WorkflowEngine
import asyncio
import json
import random

class AgentNode(Node):
    async def prepare(self, _, queue):
        message = "Hello from agent node!"
        return message
        
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"] = execution_result
    
    
class TestNode(Node):
    async def prepare(self, _, queue):
        return "Hello from test node!"
        
    def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"] = execution_result
    
# Example usage:
async def main():
    
    workflow = WorkflowEngine(json_path="workflow.json")
    
    # Continue execution
    while True:
        state = await workflow.step()
        print(state)
        if not state.current_node_ids:
            break
    
    print("\nFinal state:", workflow.execution_state.to_dict())  # Changed to access execution_state directly

if __name__ == "__main__":
    asyncio.run(main())