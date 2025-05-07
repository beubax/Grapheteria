from typing import List

class ToolManager:
    """
    Manages the tools that can be used in workflows.
    Handles tool registration, authentication, and retrieval.
    """    
    def list_available_tools(self) -> List[str]:
        pass
    
    def authenticate_tool(self, tool_name: str) -> bool:
        pass
            
    def get_authenticated_tools(self) -> List[str]:
        pass