from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


mcp_server_url = "http://localhost:8000/mcp"

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
    ),
)

root_agent = Agent(
    name="tool_agent",
    model="gemini-2.0-flash",
    description="Tool agent",
    instruction="""
    You are a helpful assistant that can use various tools.
    """,
    tools=[mcp_toolset]
)
