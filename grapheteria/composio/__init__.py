from functools import lru_cache
import json
from typing import List
import os
import webbrowser
from composio_openai import ComposioToolSet, App
from grapheteria.generator.tool_manager import ToolManager as BaseToolManager


class ToolManager(BaseToolManager):
    """
    Manages the tools that can be used in workflows.
    Handles tool registration, authentication, and retrieval.
    """
    
    def __init__(self):
        """
        Initialize the tool manager.
        
        Args:
            config_path: Path to the tool configuration file
        """
        self.toolset = ComposioToolSet()    
        self.tools = self.get_all_tools()

    #Quick lookup for all tools
    @lru_cache(maxsize=1)
    def get_all_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool names
        """
        tools_path = os.path.join(os.path.dirname(__file__), "tools.json")
        with open(tools_path, "r") as f:
            tools = json.load(f)
        return tools
    
    def authenticate_tool(self, tool_name: str) -> bool:
        """
        Authenticate with a specific tool.
        
        Args:
            tool_name: Name of the tool to authenticate with
            credentials: Authentication credentials (if required)
            
        Returns:
            True if authentication was successful, False otherwise
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        auth_scheme = self.tools[tool_name]

        if auth_scheme == "NO_AUTH":
            return True
        
        if auth_scheme != "OAUTH2":
            print("Please complete this integration in the Composio dashboard")
            return False

        entity = self.toolset.get_entity(id="default")

        tool_enum = getattr(App, tool_name.upper())

        # Perform authentication
        connection_request = entity.initiate_connection(
            app_name=tool_enum
        )

        # Composio returns a redirect URL for OAuth flows
        if connection_request.redirectUrl:
            print(f"Please visit: {connection_request.redirectUrl} to authenticate with {tool_name}")
            try:
                webbrowser.open(connection_request.redirectUrl)
                print("Browser opened automatically. If it didn't open, please copy and paste the URL manually.")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")

        # Wait for the user to complete the OAuth flow in their browser

        print("Waiting for connection to become active...")

        try:

            # This polls until the connection status is ACTIVE or timeout occurs

            active_connection = connection_request.wait_until_active(

                client=self.toolset.client, # Pass the underlying client

                timeout=120 # Wait for up to 2 minutes

            )

            print(f"Connection successful! ID: {active_connection.id}")

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
        connected_accounts = self.toolset.get_connected_accounts()

        # Return tools that are either ACTIVE or don't require authentication (NO_AUTH)
        authenticated_tools = [account.appName for account in connected_accounts if account.status == "ACTIVE"]

        print(authenticated_tools)
        
        # Add tools that don't require authentication from self.tools dictionary
        no_auth_tools = [tool_name for tool_name, auth_type in self.tools.items() if auth_type == "NO_AUTH"]
        
        return authenticated_tools + no_auth_tools

    def get_tool_info(self, tool_name: str) -> dict:
        """
        Get information about a tool.
        
        Args:
            tool_name: Name of the tool to get info for
            
        Returns:
            Dictionary of tool info
        """
        tool_enum = getattr(App, tool_name.upper())
        return self.toolset.get_tools(apps=[tool_enum])
    
    def list_available_tools(self):
        all_tools = self.tools
        authenticated_tools = self.get_authenticated_tools()
        print("Available tools:")
        for tool_name in all_tools:
            authenticated = "✓" if tool_name in authenticated_tools else "✗"
            print(f"  - {tool_name} ({authenticated})")