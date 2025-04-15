# nodes.py
import asyncio
from mcp import ClientSession, StdioServerParameters, stdio_client
from utils import call_llm
from grapheteria import Node

class QuestionNode(Node):
    async def prepare(self, shared, request_input):
        question = await request_input(
            prompt="What would you like to know?",
            input_type="text"
        )

        shared["question"] = question
        shared["messages"] = shared.get("messages", [])
        shared["messages"].append({
            "role": "user",
            "content": question
        })

class CollectMCPToolsNode(Node):
    async def prepare(self, shared, _):
        server_params = StdioServerParameters(
        command="python",
        args=["examples/mcp_tool_calling/mcp_server.py"],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                # Get tools
                response = await session.list_tools()
        
        shared["tools"] = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]  
        shared["collected_tools"] = True
        
class InitialResponseNode(Node):
    async def prepare(self, shared, request_input):
        tools = shared["tools"]
        messages = shared["messages"]
        return tools, messages
        
    async def execute(self, prep_result):             
        tools, messages = prep_result
              
        response = call_llm(messages, tools)
    
        return response
    
    def cleanup(self, shared, prep_result, exec_result): 
        tool_calls = []
        for content in exec_result.content:
            if content.type == 'tool_use':
                tool_call = {
                    "id": content.id,
                    "name": content.name,
                    "input": content.input
                }
                tool_calls.append(tool_call)

        shared["tool_calls"] = tool_calls
        messages = shared["messages"]
        messages.append({
            "role": "assistant",
            "content": exec_result.content
        })
        shared["messages"] = messages

#Parallel Tool Execution
class ToolExecutionNode(Node):
    async def prepare(self, shared, request_input):    
        tool_calls = shared["tool_calls"]
        return tool_calls
    
    async def _execute_with_retry(self, items):
        # Process all items in parallel
        tasks = [self._process_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for exceptions
        for result in results:
            if isinstance(result, Exception):
                raise result
                
        return results

    async def execute(self, prep_result):
        tool_id, tool_name, tool_input = prep_result['id'], prep_result['name'], prep_result['input']

        server_params = StdioServerParameters(
        command="python",
        args=["examples/mcp_tool_calling/mcp_server.py"],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                # Execute the tool
                result = await session.call_tool(tool_name, tool_input)

        
        return {
            "tool_use_id": tool_id,
            "result": result.content
        }
    
    def cleanup(self, shared, prep_result, exec_result):
        for result in exec_result:
            shared["messages"].append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": result["tool_use_id"],
                        "content": result["result"]
                    }
                ]
            })

class FinalResponseNode(Node):
    async def prepare(self, shared, request_input):
        messages = shared["messages"]
        tools = shared["tools"]

        return messages, tools
    
    async def execute(self, prep_result): 
        messages, tools = prep_result
        # Get final response from Claude
        response = call_llm(messages, tools)
        return response.content[0].text
    
    def cleanup(self, shared, prep_result, exec_result):
        shared["final_response"] = exec_result

class FeedbackNode(Node):
    async def prepare(self, shared, request_input):
        global _mcp_client
        print("\n🔍 Response:\n")
        print(f"Question: {shared['question']}")
        
        print("\nAnswer:")
        print(shared['final_response'])
        
        feedback = await request_input(
            prompt="Was this answer helpful?",
            options=["yes", "no"],
            input_type="select"
        )     
        shared["feedback"] = feedback
