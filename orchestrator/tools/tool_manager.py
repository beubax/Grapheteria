import os
import json
from typing import Dict, Any, List, Optional, Type, Set

from orchestrator.tools.composio_tools import ComposioTool, GmailTool, SlackTool


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
        self.config_path = config_path or os.path.expanduser("~/.orchestrator/tools.json")
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Initialize tool registry with built-in tools
        self.tool_registry = {
            "gmail": GmailTool(),
            "slack": SlackTool()
        }
        
        # Load saved configurations
        self.tool_configs = self._load_configs()
        
        # Apply configurations to tools
        self._apply_configs()
    
    def _load_configs(self) -> Dict[str, Any]:
        """
        Load tool configurations from the config file.
        
        Returns:
            Dictionary of tool configurations
        """
        if not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_configs(self) -> None:
        """Save tool configurations to the config file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.tool_configs, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save tool configurations: {e}")
    
    def _apply_configs(self) -> None:
        """Apply saved configurations to registered tools."""
        for tool_name, config in self.tool_configs.items():
            if tool_name in self.tool_registry:
                tool = self.tool_registry[tool_name]
                # Apply configuration
                if "connection_id" in config:
                    tool.connection_id = config.get("connection_id")
                if "authenticated" in config:
                    tool.authenticated = config.get("authenticated", False)
    
    def register_tool(self, tool_name: str, tool: ComposioTool) -> None:
        """
        Register a new tool.
        
        Args:
            tool_name: Name of the tool
            tool: Tool instance
        """
        self.tool_registry[tool_name] = tool
    
    def list_available_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool names
        """
        return list(self.tool_registry.keys())
    
    def get_tool(self, tool_name: str) -> Optional[ComposioTool]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self.tool_registry.get(tool_name)
    
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
            "name": tool_name,
            "description": tool.description,
            "authenticated": tool.authenticated,
            "connection_id": tool.connection_id,
            "auth_required": tool.auth_required
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
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        
        # Perform authentication
        result = tool.authenticate(credentials)
        
        # Update and save configuration
        if result:
            if tool_name not in self.tool_configs:
                self.tool_configs[tool_name] = {}
            
            self.tool_configs[tool_name].update({
                "authenticated": True,
                "connection_id": tool.connection_id
            })
            
            self._save_configs()
        
        return result
    
    def get_authenticated_tools(self) -> List[str]:
        """
        Get a list of tools that are currently authenticated.
        
        Returns:
            List of authenticated tool names
        """
        return [name for name, tool in self.tool_registry.items() if tool.authenticated] 