from grapheteria import Node
import re
from typing import Dict, Any, Optional, List

class UserInputNode(Node):
    async def prepare(self, shared, request_input):
        user_message = await request_input(prompt="What would you like to ask?")
        return user_message
        
    def execute(self, user_input):
        return user_input
        
    def cleanup(self, shared, prepared_result, execution_result):
        shared["user_input"] = execution_result
        return execution_result

class AgentNode(Node):
    async def prepare(self, shared, request_input):
        return shared.get("user_input", "")
    
    async def execute(self, user_input):
        # In a real implementation, you would call your LLM API here
        response = f"This is a response to: {user_input}"
        
        # Check if search is needed
        needs_search = "[search]" in user_input.lower()
        search_query = self.extract_search_query(user_input) if needs_search else None
        
        return {
            "response": response,
            "needs_search": needs_search,
            "search_query": search_query
        }
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["agent_response"] = execution_result["response"]
        shared["needs_search"] = execution_result["needs_search"]
        shared["search_query"] = execution_result["search_query"]
        return execution_result
    
    def extract_search_query(self, text):
        # Extract search query between brackets
        match = re.search(r'\[search\](.*?)\[/search\]', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text  # Default to using the whole text

class SearchNode(Node):
    async def prepare(self, shared, request_input):
        if not shared.get("needs_search", False):
            return None
        return shared.get("search_query", "")
    
    async def execute(self, query):
        if not query:
            return {"results": "No search query provided"}
        
        # In a real implementation, you would call a search API
        try:
            async with aiohttp.ClientSession() as session:
                # This is a placeholder, replace with actual search API
                search_url = f"https://example.com/search?q={query}"
                async with session.get(search_url) as response:
                    results = await response.text()
                    return {"results": f"Search results for '{query}'"}
        except Exception as e:
            return {"results": f"Search failed: {str(e)}"}
    
    def cleanup(self, shared, prepared_result, execution_result):
        if prepared_result:  # Only if search was performed
            shared["search_results"] = execution_result["results"]
        return execution_result

class GuardrailsNode(Node):
    async def prepare(self, shared, request_input):
        response = shared.get("agent_response", "")
        search_results = shared.get("search_results", "")
        
        # Combine agent response with search results if available
        if search_results:
            final_response = f"{response}\n\nBased on search results: {search_results}"
        else:
            final_response = response
            
        return final_response
    
    def execute(self, response):
        # Apply content filtering
        filtered_response = self.filter_content(response)
        return filtered_response
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared["final_response"] = execution_result
        return execution_result
    
    def filter_content(self, text):
        # Simple implementation - would use more sophisticated guardrails in production
        inappropriate_terms = ["offensive", "harmful", "illegal"]
        filtered_text = text
        for term in inappropriate_terms:
            filtered_text = filtered_text.replace(term, "[filtered]")
        return filtered_text

class ResponseNode(Node):
    async def prepare(self, shared, request_input):
        return shared.get("final_response", "Sorry, I couldn't process your request.")
    
    async def execute(self, response):
        return response
    
    def cleanup(self, shared, prepared_result, execution_result):
        # Present the response to the user
        shared["conversation_history"] = shared.get("conversation_history", [])
        shared["conversation_history"].append({
            "user": shared.get("user_input", ""),
            "agent": execution_result
        })
        return execution_result