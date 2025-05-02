import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
import inspect
import json


class ComposioTool:
    """
    Base class for Composio tool integrations.
    This class serves as a wrapper around Composio's tool functions.
    """
    
    def __init__(self):
        """Initialize the Composio tool."""
        self.name = "unknown"
        self.description = "Generic Composio tool"
        self.authenticated = False
        self.connection_id = None
        self.auth_required = True
    
    def authenticate(self, credentials: Dict[str, Any] = None) -> bool:
        """
        Authenticate with the tool.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement authenticate")
    
    def check_auth(self) -> bool:
        """
        Check if the tool is authenticated.
        
        Returns:
            True if the tool is authenticated, False otherwise
        """
        raise NotImplementedError("Subclasses must implement check_auth")
    
    async def _call_function(self, func_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a Composio tool function.
        
        Args:
            func_name: Name of the function to call
            params: Parameters for the function
            
        Returns:
            Function result
        """
        raise NotImplementedError("Subclasses must implement _call_function")


class GmailTool(ComposioTool):
    """
    Composio Gmail integration.
    Provides access to Gmail API functions.
    """
    
    def __init__(self):
        """Initialize the Gmail tool."""
        super().__init__()
        self.name = "gmail"
        self.description = "Gmail API integration via Composio"
        self.functions = {
            "fetch_emails": "mcp_gmail_composio_GMAIL_FETCH_EMAILS",
            "send_email": "mcp_gmail_composio_GMAIL_SEND_EMAIL",
            "fetch_message_by_thread_id": "mcp_gmail_composio_GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
            "get_attachment": "mcp_gmail_composio_GMAIL_GET_ATTACHMENT",
            "get_profile": "mcp_gmail_composio_GMAIL_GET_PROFILE",
            "fetch_message_by_message_id": "mcp_gmail_composio_GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            "create_email_draft": "mcp_gmail_composio_GMAIL_CREATE_EMAIL_DRAFT",
            "reply_to_thread": "mcp_gmail_composio_GMAIL_REPLY_TO_THREAD",
            "modify_thread_labels": "mcp_gmail_composio_GMAIL_MODIFY_THREAD_LABELS",
            "list_threads": "mcp_gmail_composio_GMAIL_LIST_THREADS",
            "check_active_connection": "mcp_gmail_composio_GMAIL_CHECK_ACTIVE_CONNECTION",
            "initiate_connection": "mcp_gmail_composio_GMAIL_INITIATE_CONNECTION",
            "get_required_parameters": "mcp_gmail_composio_GMAIL_GET_REQUIRED_PARAMETERS"
        }
        
        # Create methods dynamically for each function
        for func_name, tool_name in self.functions.items():
            setattr(self, func_name, self._create_method(func_name, tool_name))
    
    def _create_method(self, func_name: str, tool_name: str) -> Callable:
        """
        Create a method for the function.
        
        Args:
            func_name: Name of the function
            tool_name: Name of the Composio tool
            
        Returns:
            Function that calls the Composio tool
        """
        async def method(params: Dict[str, Any] = None) -> Dict[str, Any]:
            params = params or {}
            return await self._call_function(tool_name, {"params": params})
        
        return method
    
    def authenticate(self, credentials: Dict[str, Any] = None) -> bool:
        """
        Authenticate with Gmail.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        try:
            # Use synchronous wrapper to call the async method
            result = asyncio.run(self.initiate_connection({"tool": "gmail"}))
            
            if result.get("success", False):
                self.connection_id = result.get("connection_id")
                self.authenticated = True
                return True
            
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def check_auth(self) -> bool:
        """
        Check if the Gmail tool is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.connection_id:
            return False
        
        try:
            # Use synchronous wrapper to call the async method
            result = asyncio.run(self.check_active_connection({
                "tool": "gmail",
                "connection_id": self.connection_id
            }))
            
            self.authenticated = result.get("success", False)
            return self.authenticated
        except Exception:
            return False
    
    async def _call_function(self, func_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a Gmail API function.
        
        Args:
            func_name: Name of the function to call
            params: Parameters for the function
            
        Returns:
            Function result
        """
        # In a real implementation, this would call the Composio API
        # For now, we'll simulate with a mock response
        params = params or {}
        
        # Dynamically get the corresponding method from globals (would be replaced with actual SDK call)
        if func_name in globals():
            method = globals()[func_name]
            if inspect.iscoroutinefunction(method):
                return await method(params)
            else:
                return method(params)
        
        # Mock response for demonstration
        return {
            "success": True,
            "result": f"Called {func_name} with params {json.dumps(params)}",
            "connection_id": self.connection_id or "mock_connection_id"
        }


class SlackTool(ComposioTool):
    """
    Composio Slack integration.
    Provides access to Slack API functions.
    """
    
    def __init__(self):
        """Initialize the Slack tool."""
        super().__init__()
        self.name = "slack"
        self.description = "Slack API integration via Composio"
        self.functions = {
            "send_message": "mcp_slack_composio_SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
            "search_messages": "mcp_slack_composio_SLACK_SEARCH_FOR_MESSAGES_WITH_QUERY",
            "fetch_conversation_history": "mcp_slack_composio_SLACK_FETCH_CONVERSATION_HISTORY",
            "list_users": "mcp_slack_composio_SLACK_USERS_LIST",
            "find_user_by_email": "mcp_slack_composio_SLACK_FIND_USER_BY_EMAIL_ADDRESS",
            "post_message": "mcp_slack_composio_SLACK_CHAT_POST_MESSAGE",
            "conversations_history": "mcp_slack_composio_SLACK_CONVERSATIONS_HISTORY",
            "share_me_message": "mcp_slack_composio_SLACK_SHARE_A_ME_MESSAGE_IN_A_CHANNEL",
            "delete_channel": "mcp_slack_composio_SLACK_DELETE_A_PUBLIC_OR_PRIVATE_CHANNEL",
            "users_info": "mcp_slack_composio_SLACK_USERS_INFO",
            "check_active_connection": "mcp_slack_composio_SLACK_CHECK_ACTIVE_CONNECTION",
            "initiate_connection": "mcp_slack_composio_SLACK_INITIATE_CONNECTION",
            "get_required_parameters": "mcp_slack_composio_SLACK_GET_REQUIRED_PARAMETERS"
        }
        
        # Create methods dynamically for each function
        for func_name, tool_name in self.functions.items():
            setattr(self, func_name, self._create_method(func_name, tool_name))
    
    def _create_method(self, func_name: str, tool_name: str) -> Callable:
        """
        Create a method for the function.
        
        Args:
            func_name: Name of the function
            tool_name: Name of the Composio tool
            
        Returns:
            Function that calls the Composio tool
        """
        async def method(params: Dict[str, Any] = None) -> Dict[str, Any]:
            params = params or {}
            return await self._call_function(tool_name, {"params": params})
        
        return method
    
    def authenticate(self, credentials: Dict[str, Any] = None) -> bool:
        """
        Authenticate with Slack.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        try:
            # Use synchronous wrapper to call the async method
            result = asyncio.run(self.initiate_connection({"tool": "slack"}))
            
            if result.get("success", False):
                self.connection_id = result.get("connection_id")
                self.authenticated = True
                return True
            
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def check_auth(self) -> bool:
        """
        Check if the Slack tool is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.connection_id:
            return False
        
        try:
            # Use synchronous wrapper to call the async method
            result = asyncio.run(self.check_active_connection({
                "tool": "slack",
                "connection_id": self.connection_id
            }))
            
            self.authenticated = result.get("success", False)
            return self.authenticated
        except Exception:
            return False
    
    async def _call_function(self, func_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a Slack API function.
        
        Args:
            func_name: Name of the function to call
            params: Parameters for the function
            
        Returns:
            Function result
        """
        # In a real implementation, this would call the Composio API
        # For now, we'll simulate with a mock response
        params = params or {}
        
        # Dynamically get the corresponding method from globals (would be replaced with actual SDK call)
        if func_name in globals():
            method = globals()[func_name]
            if inspect.iscoroutinefunction(method):
                return await method(params)
            else:
                return method(params)
        
        # Mock response for demonstration
        return {
            "success": True,
            "result": f"Called {func_name} with params {json.dumps(params)}",
            "connection_id": self.connection_id or "mock_connection_id"
        } 