# Advanced Node Types

## Beyond the Basics: Supercharging Your Nodes

Sometimes a simple node just doesn't cut it. Whether you need to fetch data from multiple APIs simultaneously or process a batch of items, the `Node` class has got your back. Let's explore how to take your nodes from "meh" to "magnificent"!

## Embracing Asynchrony: The Async Magic

Any of the core node methods - `prepare`, `execute`, or `cleanup` - can be async. Just slap on that `async` keyword and you're good to go:

```python
class AsyncFetchNode(Node):
    async def execute(self, prepared_result):
        # Look at me, I'm async!
        await asyncio.sleep(1)  # Simulating network delay
        return {"data": "Fetched asynchronously"}
```

The workflow engine knows how to handle these async methods and will await them properly. No need to worry about the plumbing!

## Going Parallel: Multi-tasking Like a Pro

Want to run multiple operations at the same time? Extend the `_execute_with_retry` method:

```python
class ParallelNode(Node):
    async def prepare(self, shared, request_input):
        # Return a list of items to process in parallel
        return [{"id": i} for i in range(5)]
        
    async def _execute_with_retry(self, items):
        # Process all items in parallel
        tasks = [self._process_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for exceptions
        for result in results:
            if isinstance(result, Exception):
                raise result
                
        return results
        
    async def execute(self, item):
        # Process a single item
        await asyncio.sleep(1)  # Simulate work
        return f"Processed item {item['id']}"
        
    def cleanup(self, shared, prepared_result, execution_result):
        # Initialize results list if it doesn't exist
        if "parallel_results" not in shared:
            shared["parallel_results"] = []
        
        # Append new results to existing list
        shared["parallel_results"].extend(execution_result)
        return execution_result
```

This node will process all items simultaneously, making your workflow zip along at warp speed!

## Batch Processing: Same Task, Different Data

Don't need the complexity of parallelism but want to process multiple items? Batch processing is your friend:

```python
class BatchNode(Node):
    def prepare(self, shared, request_input):
        # Return batch of items to process
        return [f"item-{i}" for i in range(10)]
    
    async def _execute_with_retry(self, items):
        # Process each item in batch sequentially
        results = []
        for item in items:
            # Process each item with potential retries
            result = await super()._process_item(item)
            results.append(result)
        return results
        
    def execute(self, item):
        # Process a single item
        return f"Processed {item}"
        
    def cleanup(self, shared, prepared_result, execution_result):
        # Initialize results dictionary if needed
        if "batch_results" not in shared:
            shared["batch_results"] = []
            
        # Add latest batch results
        shared["batch_results"].extend(execution_result)
        return execution_result
```

## Error Handling in Advanced Nodes

Currently, if any task in a parallel or batch node fails, the entire node fails. This "fail fast" approach keeps things simple and predictable.

```python
class ParallelWithErrorNode(Node):
    async def prepare(self, shared, request_input):
        return [1, 2, 0, 4]  # That zero will cause trouble!
        
    async def execute(self, item):
        # This will fail for item == 0
        result = 10 / item
        return result
        
    def exec_fallback(self, prepared_result, exception):
        # This will run if execute fails
        return f"Failed to process items: {exception}"
```

If you need more sophisticated error handling (like continuing despite errors in some items), feel free to raise an issue on GitHub. We're always looking to improve!

Remember: these advanced nodes follow the same lifecycle as basic nodes, just with superpowers. Mix and match these techniques to create workflows that handle real-world complexity with grace!