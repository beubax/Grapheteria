from functools import lru_cache
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@lru_cache(maxsize=1)
def get_llm_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def call_llm(prompt, max_tokens=500):
    """Call OpenAI's API to generate text."""
    llm_client = get_llm_client()
    
    try:
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful article writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Failed to generate article about {prompt}"

