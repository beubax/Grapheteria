# main.py
from examples.mcp_tool_calling.nodes import *
from grapheteria import WorkflowEngine
import asyncio

# Create nodes
question = QuestionNode(id="question")
collect_mcp_tools = CollectMCPToolsNode(id="collect_mcp_tools")
initial_response = InitialResponseNode(id="initial_response")
tool_execution = ToolExecutionNode(id="tool_execution")
final_response = FinalResponseNode(id="final_response")
feedback = FeedbackNode(id="feedback")

# Connect nodes to form workflow
question > collect_mcp_tools > initial_response > final_response
question - "shared.get('collected_tools', False) == True" > initial_response
initial_response - "shared.get('tool_calls', False)" > tool_execution > final_response
final_response > feedback
feedback - "shared['feedback'] == 'no'" > question

# Create the workflow engine    
workflow = WorkflowEngine(
    workflow_id="mcp_tool_calling",
    nodes=[question, collect_mcp_tools, initial_response, tool_execution, final_response, feedback],
    start=question
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
    print("🧠 Claude Research Assistant with MCP Tools")
    print("------------------------------------------")
    print("Ask me anything! I can use tools to help you.")
    
    # Run the workflow
    asyncio.run(run_workflow())
