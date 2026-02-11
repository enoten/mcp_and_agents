from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands import tool
import argparse

parser = argparse.ArgumentParser(
        description="Some Script"
    )
parser.add_argument("--query", required=True, type=str)

args = parser.parse_args()
if args:
    query = args.query

streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client("http://localhost:8003/mcp")
)

@tool
def list_mcp_tools():
    """
    Return list of mcp tools provide by the mcp server
    
    :param streamable_http_mcp_client: streamable_http_mcp_client
    """
    tools_list = streamable_http_mcp_client.list_tools_sync()
    tools_list_str = []
    for tool in tools_list:
        tool_info = tool.get_display_properties()
        tools_list_str.append(tool_info["Name"])
    return tools_list_str


with streamable_http_mcp_client:
    mcp_tools = streamable_http_mcp_client.list_tools_sync()
    #print(">>>>>>",mcp_tools[0].get_display_properties())
    agent = Agent(tools=[mcp_tools,list_mcp_tools])
    
    #1. cross currency rate
    agent(query)