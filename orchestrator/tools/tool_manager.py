import os
import json
from typing import Dict, Any, List, Optional, Type, Set
from composio import ComposioToolSet
from orchestrator.tools.tool_enums import get_tool_enums


class ToolManager:
    """
    Manages the tools that can be used in workflows.
    Handles tool registration, authentication, and retrieval.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the tool manager.
        
        Args:
            config_path: Path to the tool configuration file
        """
        self.tool_config_path = config_path or os.path.join(os.path.dirname(__file__), "tools.json")
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.tool_config_path), exist_ok=True)
        
        # Load saved configurations
        self.tools = self._load_configs()

    def _load_configs(self) -> Dict[str, Any]:
        """
        Load tool configurations from the config file.
        
        Returns:
            Dictionary of tool configurations
        """
        if not os.path.exists(self.tool_config_path):
            return {}
        
        try:
            with open(self.tool_config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_configs(self) -> None:
        """Save tool configurations to the config file."""
        try:
            with open(self.tool_config_path, "w") as f:
                json.dump(self.tools, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save tool configurations: {e}")
    
    def list_available_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_tool(self, tool_name: str) -> Optional[ComposioTool]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self.tools.get(tool_name)
    
    def get_tool_details(self, tool_name: str) -> Dict[str, Any]:
        """
        Get details about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool details
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        
        return {
            "authenticated": self.tools[tool_name].get("authenticated"),
        }
    
    def authenticate_tool(self, tool_name: str, credentials: Dict[str, Any] = None) -> bool:
        """
        Authenticate with a specific tool.
        
        Args:
            tool_name: Name of the tool to authenticate with
            credentials: Authentication credentials (if required)
            
        Returns:
            True if authentication was successful, False otherwise
        """
        tool_enum = get_tool_enums(tool_name)
        if not tool_enum:
            return False
        
        toolset = ComposioToolSet()

        entity = toolset.get_entity(id="default")

        # Perform authentication
        connection_request = entity.initiate_connection(
            app_name=tool_enum
        )

        # Composio returns a redirect URL for OAuth flows

        if connection_request.redirectUrl:
            print(f"Please visit: {connection_request.redirectUrl} to authenticate with {tool_name}")

        # Wait for the user to complete the OAuth flow in their browser

        print("Waiting for connection to become active...")

        try:

            # This polls until the connection status is ACTIVE or timeout occurs

            active_connection = connection_request.wait_until_active(

                client=toolset.client, # Pass the underlying client

                timeout=120 # Wait for up to 2 minutes

            )

            print(f"Connection successful! ID: {active_connection.id}")

            if tool_name not in self.tools:
                self.tools[tool_name] = {}
            
            self.tools[tool_name].update({
                "authenticated": True,
                "connection_id": active_connection.id
            })

            self._save_configs()

            return True

        except Exception as e:

            print(f"Connection timed out or failed: {e}")

            return False
    
    def get_authenticated_tools(self) -> List[str]:
        """
        Get a list of tools that are currently authenticated.
        
        Returns:
            List of authenticated tool names
        """
        return [name for name in self.tools.keys() if self.tools[name].get("authenticated")] 