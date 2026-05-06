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
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()]
    )

asyncio.run(main())