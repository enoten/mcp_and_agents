import asyncio
from strands.experimental.bidi import BidiAgent, BidiAudioIO
from strands.experimental.bidi.models import BidiNovaSonicModel


# Create agent with tools
model = BidiNovaSonicModel()
agent = BidiAgent(
    model=model,
    system_prompt="You are a helpful assistant."
)

audio_io = BidiAudioIO()

async def main():
    print("Start chatting with the Agent")
    try:
        # Runs indefinitely until interrupted
        await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()]
        )
    except asyncio.CancelledError:
        print("\nConversation cancelled by user")
    finally:
        # stop() should only be called after run() exits
        await agent.stop()
asyncio.run(main())