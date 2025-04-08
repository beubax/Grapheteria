# import requests
# import json
# from typing import Dict, Any, List, Optional
from grapheteria import Node

class Agent(Node):
    def execute(self, prepared_result):
        pass


class Tool(Node):
    def execute(self, prepared_result):
        pass

class Response(Node):
    def execute(self, prepared_result):
        pass

# class UserInputNode(Node):
#     async def prepare(self, shared, request_input):
#         user_input = await request_input(prompt="What would you like to ask?")
#         return user_input
        
#     def execute(self, user_input):
#         return user_input
        
#     def cleanup(self, shared, prepared_result, execution_result):
#         shared["user_input"] = execution_result
#         shared["messages"] = shared.get("messages", []) + [{"role": "user", "content": execution_result}]
#         return execution_result

# class RouterNode(Node):
#     def execute(self, prepared_result):
#         # Determine if the query needs internet search
#         user_input = prepared_result
#         search_keywords = ["search", "find", "lookup", "latest", "news", "information", "data", "weather", "current"]
#         needs_search = any(keyword in user_input.lower() for keyword in search_keywords)
#         return needs_search
        
#     def cleanup(self, shared, prepared_result, execution_result):
#         shared["needs_search"] = execution_result
#         return execution_result

# class InternetSearchNode(Node):
#     def prepare(self, shared, request_input):
#         return shared["user_input"]
    
#     def execute(self, query):
#         try:
#             # Simple mock search implementation
#             # In production, replace with actual search API
#             url = f"https://api.duckduckgo.com/?q={query}&format=json"
#             response = requests.get(url)
#             results = response.json()
#             return {"query": query, "results": results}
#         except Exception as e:
#             return {"query": query, "error": str(e), "results": "No results found"}
    
#     def cleanup(self, shared, prepared_result, execution_result):
#         shared["search_results"] = execution_result
#         return execution_result

# class LLMResponseNode(Node):
#     def prepare(self, shared, request_input):
#         messages = shared.get("messages", [])
#         search_results = shared.get("search_results", None)
        
#         if search_results:
#             # Include search results in context
#             context = f"Search results for '{search_results['query']}':\n"
#             context += json.dumps(search_results["results"], indent=2)[:1000] + "..."
#             messages.append({"role": "system", "content": context})
            
#         return messages
    
#     def execute(self, messages):
#         # This is a mock LLM implementation
#         # Replace with actual LLM API call in production
#         last_message = messages[-1]["content"] if messages else ""
#         if "search_results" in messages[-1]["content"]:
#             return f"Based on my search, I found that {last_message}. Is there anything else you'd like to know?"
#         return f"You asked: '{last_message}'. Here's my response. Would you like to know more?"
    
#     def cleanup(self, shared, prepared_result, execution_result):
#         shared["llm_response"] = execution_result
#         shared["messages"] = shared.get("messages", []) + [{"role": "assistant", "content": execution_result}]
#         return execution_result

# class ContinueConversationNode(Node):
#     async def prepare(self, shared, request_input):
#         continue_convo = await request_input(
#             prompt="Would you like to continue the conversation?",
#             options=["Yes", "No"],
#             input_type="select"
#         )
#         return continue_convo
        
#     def execute(self, continue_convo):
#         return continue_convo == "Yes"
        
#     def cleanup(self, shared, prepared_result, execution_result):
#         shared["continue_conversation"] = execution_result
#         return execution_result




