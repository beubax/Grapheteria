from machine import Node

class TejasNode(Node):
    async def prepare(self, _, queue):
        message = "Hello from agent node!"
        return message
        
    async def execute(self, prepared_result):
        # Required implementation of abstract method
        return prepared_result
    
    async def cleanup(self, shared, prepared_result, execution_result):
        shared["messages"].append("Agent NODE")

class TrishaNode(Node):
    async def prepare(self, _, queue):
        return "Hello from TestNode!"
    
    async def execute(self, prepared_result):
        return prepared_result
