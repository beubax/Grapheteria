from composio import App
import json
enums = {
    "GITHUB": App.GITHUB,
    "SLACK": App.SLACK
}

def get_tool_enums(app_name: str):
    if app_name not in enums:
        raise ValueError(f"App name {app_name} not found in enums")
    return enums[app_name]



