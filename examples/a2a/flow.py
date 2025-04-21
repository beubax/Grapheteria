from grapheteria import Node, WorkflowEngine
import asyncio

class FirstNode(Node):
    def prepare(self, shared, _, stream_output=None):
        return "Hey how are you?"
    
    def cleanup(self, shared, prepared_result, execution_result, stream_output=None):
        shared["message"] = prepared_result
        print(shared)

class SecondNode(Node):
    def prepare(self, shared, _, stream_output=None):
        return "Hey I am second node"

    def cleanup(self, shared, prepared_result, execution_result, stream_output=None):
        shared["message"] = prepared_result
        print(shared)

class ThirdNode(Node):
    def prepare(self, shared, _, stream_output=None):
        return "Hey I am third node"

    def cleanup(self, shared, prepared_result, execution_result, stream_output=None):
        shared["message"] = prepared_result
        print(shared)


def create_workflow():
    first_node = FirstNode()
    second_node = SecondNode()
    third_node = ThirdNode()

    first_node > second_node > third_node

    workflow = WorkflowEngine(nodes=[first_node, second_node, third_node], start=first_node)
    return workflow

async def main():
    workflow = create_workflow()
    async for item in workflow.run():
        print(item)


if __name__ == "__main__":
    asyncio.run(main())



