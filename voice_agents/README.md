# Voice and Realtime (Root Files)

This project contains standalone Python examples for building realtime voice/text agents with AWS Strands bidirectional APIs and different model backends.

## Root Files

- `.env`  
  Local environment variables file for API keys used by provider-specific examples.

- `aws_strands_voice_agent_basic.py`  
  Minimal audio-only realtime agent using `BidiNovaSonicModel`.

- `aws_strands_voice_agent_basic_conv_control.py`  
  Audio-only realtime agent with explicit conversation lifecycle handling (`try/finally` and `agent.stop()`).

- `aws_strands_voice_agent_basic_conv_control_text_io.py`  
  Realtime agent that supports both audio and text input/output streams.

- `aws_strands_voice_agent_basic_conv_control_text_io_tools.py`  
  Audio+text agent with tools (`calculator`, `current_time`, and a custom `get_weather`) on Nova Sonic.

- `aws_strands_voice_agent_basic_conv_control_text_io_tools_OpenAI.py`  
  Audio+text tool-enabled agent using OpenAI Realtime (`BidiOpenAIRealtimeModel`).

- `aws_strands_voice_agent_basic_conv_control_text_io_tools_gemini.py`  
  Audio+text tool-enabled agent using Gemini Live (`BidiGeminiLiveModel`).

## Quick Setup

1. Create and activate a Python virtual environment.
2. Install required dependencies for Strands and dotenv.
3. Configure `.env` with the API key(s) needed for the script you run.
4. Run one script directly, for example:

```bash
python aws_strands_voice_agent_basic.py
```

## Notes

- These root scripts are example entry points and are intended to be run independently.
- Provider-specific scripts require corresponding API keys in `.env`.
- The `copy/` directory contains additional variants and is intentionally not covered in this README.
