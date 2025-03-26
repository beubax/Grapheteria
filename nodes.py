from machine import Node

class AgentNode(Node):
    async def prepare(self, state, request_input):
        message = "Hello from agent node"
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