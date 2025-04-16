# utils.py
from functools import lru_cache
from typing import Dict, Any, List
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

@lru_cache(maxsize=1)
def get_llm_client():
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> str:
    llm_client = get_llm_client()
    response = llm_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=tools
        )
    return response
