from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


#mcp_server_url = "http://localhost:8003/mcp"
mcp_server_url="https://nonrepresentational-anne-tantalizingly.ngrok-free.dev/mcp"
 
mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
    ),
)

root_agent = Agent(
    name="sampling_llm_agent",
    model="gemini-2.0-flash",
    description="Tool agent",
    instruction="""
    You are a helpful assistant that can use various tools.
    """,
    tools=[mcp_toolset]
)
