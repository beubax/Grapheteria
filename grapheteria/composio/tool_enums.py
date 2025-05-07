from composio import App
enums = {
    "github": {
        "app": App.GITHUB,
        "auth_scheme": "OAUTH"
    },
    "slack": {
        "app": App.SLACK,
        "auth_scheme": "OAUTH"
    },
    "gmail": {
        "app": App.GMAIL,
        "auth_scheme": "OAUTH"
    },
    "firecrawl": {
        "app": App.FIRECRAWL,
        "auth_scheme": "API_KEY"
    }
}

def get_tool_enums(app_name: str):
    if app_name not in enums:
        raise ValueError(f"App name {app_name} not found in enums")
    return enums[app_name]


def get_tool_enums_list():
    return list(enums.keys())


