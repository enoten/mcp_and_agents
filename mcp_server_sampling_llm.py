from fastmcp import FastMCP, Context
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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

# @mcp.tool()
# async def write_summary(text: str):
#     """USe this tool to generate summary of the text or content"""
#     # This will now work! 
#     # It tries ADK first, fails, then uses your Gemini API key.
#     ctx = Context(fastmcp=mcp)
#     result = await ctx.sample(f"Summarize this: {text}")
#     return result.text

@mcp.tool
async def summarize(content: str, ctx: Context) -> str:
    """Generate a summary of the provided content."""
    result = await ctx.sample(f"Please summarize this:\n\n{content}")
    return result.text or ""

if __name__ == "__main__":
    mcp.run(transport="http", 
            host="0.0.0.0", 
            port=8007)