import asyncio
from strands.experimental.bidi import BidiAgent, BidiAudioIO
#from strands.experimental.bidi.models import BidiNovaSonicModel
from strands.experimental.bidi.io import BidiTextIO
from strands import tool
from strands_tools import calculator, current_time
from strands.experimental.bidi.models import BidiOpenAIRealtimeModel

# Define a custom tool
@tool
def get_weather(location: str) -> str:
    """
    Get the current weather for a location.

    Args:
        location: City name or location

    Returns:
        Weather information
    """
    # In a real application, call a weather API
    return f"The weather in {location} is sunny and 72°F"

import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Create agent with tools
#model = BidiNovaSonicModel()

model = BidiOpenAIRealtimeModel(
    model_id="gpt-realtime",
    provider_config={
        "audio": {
            "voice": "coral",
        },
    },
    client_config={"api_key": OPENAI_API_KEY},
)

agent = BidiAgent(
    model=model,
    tools=[calculator, current_time, get_weather],
    system_prompt="You are a helpful assistant with access to tools."
)


audio_io = BidiAudioIO()
text_io = BidiTextIO()


async def main():
    print("Start chatting with the Agent")
    try:
        # Runs indefinitely until interrupted
        await agent.run(
        inputs=[audio_io.input(), text_io.input()],
        outputs=[audio_io.output(), text_io.output()]
        )
    except asyncio.CancelledError:
        print("\nConversation cancelled by user")
    finally:
        # stop() should only be called after run() exits
        await agent.stop()
        
asyncio.run(main())