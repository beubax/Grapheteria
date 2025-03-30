from machine import Node, InputRequest
import aiohttp
import json
import os
import re
from typing import List, Dict, Any, Optional

class UserInputNode(Node):
    """Node that gets input from the user"""
    
    def prepare(self, shared, request_input):
        # Keep track of conversation history
        if 'conversation' not in shared:
            shared['conversation'] = []
        
        # Get input from user
        return request_input(
            prompt="What would you like to know?",
            input_type="text"
        )
    
    def execute(self, user_input):
        return user_input
    
    def cleanup(self, shared, prepared_result, execution_result):
        # Store the user query
        shared['user_query'] = execution_result
        shared['conversation'].append({"role": "user", "content": execution_result})
        return execution_result


class WebSearchNode(Node):
    """Node that searches the internet for information using Tavily API"""
    
    async def execute(self, prepared_result):
        query = self.config.get('shared_key', 'user_query')
        search_api_key = "Hello"
        
        if not search_api_key:
            return {"error": "No Tavily API key provided. Set TAVILY_API_KEY environment variable or in node config."}
        
        # Using Tavily API for search
        search_url = "https://api.tavily.com/search"
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": search_api_key
                }
                
                payload = {
                    "query": query,
                    "search_depth": "advanced",
                    "include_domains": [],
                    "exclude_domains": [],
                    "max_results": 5
                }
                
                async with session.post(search_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {"error": f"Tavily API returned status {response.status}: {error_text}"}
                    
                    data = await response.json()
                    
                    # Extract results
                    search_results = data.get("results", [])
                    formatted_results = []
                    
                    for result in search_results[:3]:  # Limit to top 3 results
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("content", ""),
                            "link": result.get("url", "")
                        })
                    
                    return formatted_results
            except Exception as e:
                return {"error": f"Error searching with Tavily: {str(e)}"}
        
    def cleanup(self, shared, prepared_result, execution_result):
        # Store search results in shared state
        shared['search_results'] = execution_result
        return execution_result

    def exec_fallback(self, prepared_result, e):
        # Fallback with mock data in case the API fails
        return [
            {"title": "Sample result", "snippet": "This is a fallback result since the Tavily search API call failed.", "link": "https://example.com"},
            {"title": "Another result", "snippet": "Another fallback result with relevant information.", "link": "https://example.org"}
        ]


class LLMResponseNode(Node):
    """Node that uses an LLM API to generate a response based on search results"""
    
    def prepare(self, shared, request_input):
        # Get the search results and user query
        search_results = shared.get('search_results', [])
        user_query = shared.get('user_query', '')
        conversation = shared.get('conversation', [])
        
        # Format search results for the LLM prompt
        formatted_results = []
        
        if isinstance(search_results, dict) and "error" in search_results:
            formatted_results.append(f"Search error: {search_results['error']}")
        else:
            for i, result in enumerate(search_results):
                formatted_results.append(
                    f"[{i+1}] {result.get('title')}\n"
                    f"URL: {result.get('link')}\n"
                    f"Summary: {result.get('snippet')}\n"
                )
        
        search_context = "\n\n".join(formatted_results)
        
        return {
            "query": user_query,
            "search_results": search_context,
            "conversation": conversation
        }
    
    async def execute(self, prepared_data):
        llm_api_key = "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"
        
        if not llm_api_key:
            return "I couldn't access my language capabilities. Please check API configuration."
        
        query = prepared_data["query"]
        search_results = prepared_data["search_results"]
        conversation = prepared_data["conversation"]
        
        # Prepare messages for the LLM
        system_prompt = """
        You are a helpful assistant that answers questions based on internet search results.
        When responding:
        1. Use the provided search results to ground your answer with facts
        2. Cite your sources using the reference numbers [1], [2], etc.
        3. If the search results don't contain relevant information, acknowledge that
        4. Be concise and helpful
        """
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add previous conversation for context (limited to last 6 messages)
        for msg in conversation[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current query with search results as context
        context_message = f"""
        The user asked: "{query}"
        
        Search results:
        {search_results}
        
        Please provide a helpful response based on these search results.
        """
        
        messages.append({"role": "user", "content": context_message})
        
        # Call OpenAI API
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}"
                }
                payload = {
                    "model": "gpt-4-turbo",  # or any other model
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 800
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error generating response: {error_text}"
                    
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
            
            except Exception as e:
                return f"Error generating response: {str(e)}"
    
    def cleanup(self, shared, prepared_result, execution_result):
        # Add the response to the conversation history
        shared['conversation'].append({"role": "assistant", "content": execution_result})
        return execution_result

    def exec_fallback(self, prepared_result, e):
        # Fallback response if the LLM API fails
        query = prepared_result.get("query", "your question")
        return f"I apologize, but I encountered an issue while generating a response about '{query}'. My language model service is currently unavailable. Please try again later."


class ContinueNode(Node):
    """Node that asks if the user wants to continue the conversation"""
    
    def prepare(self, shared, request_input):
        return request_input(
            prompt="Would you like to ask another question?",
            options=["Yes", "No"],
            input_type="options"
        )
    
    def execute(self, user_choice):
        return user_choice
    
    def cleanup(self, shared, prepared_result, execution_result):
        shared['continue_conversation'] = (execution_result == "Yes")
        return execution_result
