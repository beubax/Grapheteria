from grapheteria import Node, WorkflowEngine
from utils import call_llm

class GenerateContentNode(Node):
    async def prepare(self, shared, request_input):
        topic = await request_input(
            prompt="What topic would you like an article about?",
            input_type="text",
            request_id="generate_content"
        )
        shared["topic"] = topic 
        return topic

    def execute(self, topic):
        prompt = f"Write an informative article about {topic}"
        article = call_llm(prompt)
        return article

    def cleanup(self, shared, prep_result, exec_result):
        shared["article"] = exec_result

class HumanReviewNode(Node):
    async def prepare(self, shared, request_input):
        print(f"Article about '{shared['topic']}':")
        print(shared['article'][:150] + "...")
        
        response = await request_input(
            prompt="Do you approve this content?",
            options=["approve", "reject"],
            input_type="select"
        )
        
        shared["human_decision"] = response

class PublishNode(Node):
    async def prepare(self, shared, _):
        print(f"🎉 Publishing '{shared['topic']}' article")
        # In a real app, you might save to a database or CMS
        # await write_to_db(shared['article'])

class ReviseNode(Node):
    async def prepare(self, shared, request_input):
        print("✏️ Article needs revision")

        feedback = await request_input(
            prompt="What needs to be improved?",
            input_type="text"
        )
        return {
            'topic':shared['topic'],
            'content': shared['article'],
            'feedback': feedback
            }

    async def execute(self, data):           
        new_prompt = f"Topic: {data['topic']}. Revise this article: {data['content'][:200]}... Based on feedback: {data['feedback']}"
        revised = call_llm(new_prompt, max_tokens=700)
        return revised

    def cleanup(self, shared, prep_result, exec_result):
        shared["article"] = exec_result


def create_workflow():
    workflow = WorkflowEngine(workflow_path="examples/a2a/workflow.json")
    return workflow




