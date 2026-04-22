"""Entry point matching the short name `adk_agent_tool_selection`.

Same behavior as `adk_agent_tool_selection_steps.py` (LlmRequest.append_tools demo + runtime trace).
"""

import asyncio

from adk_agent_tool_selection_steps import main

if __name__ == "__main__":
    asyncio.run(main())
