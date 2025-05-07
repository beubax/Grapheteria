from typing import List
import webbrowser
from composio_openai import ComposioToolSet
from grapheteria.composio.tool_enums import get_tool_enums, get_tool_enums_list
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
    
    def list_all_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool names
        """
        return get_tool_enums_list()
    
    def authenticate_tool(self, tool_name: str) -> bool:
        """
        Authenticate with a specific tool.
        
        Args:
            tool_name: Name of the tool to authenticate with
            credentials: Authentication credentials (if required)
            
        Returns:
            True if authentication was successful, False otherwise
        """
        tool_details = get_tool_enums(tool_name)
        if not tool_details:
            return False
        
        auth_scheme = tool_details["auth_scheme"]  
        if auth_scheme == "API_KEY":
            print("Please complete this integration in the Composio dashboard")
            return False

        entity = self.toolset.get_entity(id="default")

        # Perform authentication
        connection_request = entity.initiate_connection(
            app_name=tool_details["app"]
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

        return [account.appName for account in connected_accounts if account.status == "ACTIVE"]
    
    def get_tool_enums(self, app_name: str) -> dict:
        """        
        Args:
            app_name: Name of the app to get tool enums for
            
        Returns:
            Dictionary of tool enums
        """
        return get_tool_enums(app_name)

    def get_tool_info(self, app_name: str) -> dict:
        """
        Get information about a tool.
        
        Args:
            app_name: Name of the app to get tool info for
            
        Returns:
            Dictionary of tool info
        """
        return self.toolset.get_tools(apps=[app_name])
    
    def list_available_tools(self):
        all_tools = self.list_all_tools()
        authenticated_tools = self.get_authenticated_tools()
        print("Available tools:")
        for tool_name in all_tools:
            authenticated = "✓" if tool_name in authenticated_tools else "✗"
            print(f"  - {tool_name} ({authenticated})")