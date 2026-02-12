from fastmcp import FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class UserInfo:
    name: str
    age: int


# Initialize the OpenAI client with your key
#openai_client = OpenAI(api_key=openai_api_key)

llm_handler = OpenAISamplingHandler(
    default_model="gpt-4o-mini",
    #client=openai_client
)

# Initialize MCP Server
mcp = FastMCP("LLM Sampling MCP",
              sampling_handler=llm_handler,
              sampling_handler_behavior="always"
              )

@mcp.tool()
async def generate_smart_filename(content: str, ctx: Context) -> str:
    """ generate a filename based on content."""
    # This sends the request BACK to the client (e.g., Claude Desktop)
    #ctx = Context(fastmcp=mcp)
    result = await ctx.sample(messages=f"Suggest a 3-word filename for this: {content}")
    
    return f"{result.text}"  or "None"


@mcp.tool
async def summarize(content: str, ctx: Context) -> str:
    """Generate a summary of the provided content."""
    result = await ctx.sample(f"Please summarize this:\n\n{content}")
    return result.text or ""

@mcp.tool
async def collect_user_info(ctx: Context) -> str:
    """Collect user information through interactive prompts."""
    result = await ctx.elicit(
        message="Please provide your information",
        response_type=UserInfo
    )
    
    if result.action == "accept":
        user = result.data
        return f"Hello {user.name}, you are {user.age} years old"
    elif result.action == "decline":
        return "Information not provided"
    else:  # cancel
        return "Operation cancelled"

if __name__ == "__main__":
    mcp.run(transport="http", 
            host="0.0.0.0", 
            port=8007)