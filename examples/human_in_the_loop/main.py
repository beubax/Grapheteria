from examples.human_in_the_loop.nodes import *
from grapheteria import WorkflowEngine
import asyncio

# Create nodes
generate = GenerateContentNode(id="generate_content")
review = HumanReviewNode(id="human_review")
publish = PublishNode(id="publish")
revise = ReviseNode(id="revise")

# Connect with conditional paths
generate > review
review - "shared['human_decision'] == 'approve'" > publish
review - "shared['human_decision'] == 'reject'" > revise
revise > review  # Loop back for another review

# Create the workflow engine
workflow = WorkflowEngine(
    nodes=[generate, review, publish, revise],
    start=generate
)

async def run_workflow():
    user_input = None
    
    while True:
        continue_workflow = await workflow.run(user_input)
        
        # If workflow is waiting for input
        if workflow.execution_state.awaiting_input:
            request = workflow.execution_state.awaiting_input
            request_id = request['request_id']
            prompt = request['prompt']
            
            print(f"\n[Input required] {prompt}")
            
            if request['input_type'] == 'select':
                for i, option in enumerate(request['options']):
                    print(f"{i+1}. {option}")
                choice = input("Enter your choice (number): ")
                user_input = request['options'][int(choice)-1]
            else:
                user_input = input("Your response: ")
            
            await workflow.step({request_id: user_input})
        elif not continue_workflow:
            break
            
            
if __name__ == "__main__":
    # Run the workflow
    asyncio.run(run_workflow())
