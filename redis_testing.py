import asyncio
import aioredis
import json

async def provide_input(workflow_id, run_id, request_id, input_value):
    # Connect to Redis
    redis = await aioredis.from_url("redis://localhost")
    
    # Format the queue name the same way
    queue_name = f"workflow:{workflow_id}:run:{run_id}:input:{request_id}"
    
    # Push the input value to the queue
    await redis.rpush(queue_name, json.dumps(input_value))
    
    # Close Redis connection
    await redis.close()

# Example usage
asyncio.run(provide_input(
    "async_demo", 
    "20250312_131307_c2612103", 
    "1741134227911", 
    {"text": "User's response", "confirmed": True}
))