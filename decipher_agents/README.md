# Decipher Agents

This README documents the `decipher_agents` examples used to learn and debug tool-calling behavior across both Google ADK and LangChain ReAct.

## Purpose

The `decipher_agents` folder focuses on understanding how an agent:

- receives a user query,
- decides whether to call a tool,
- executes that tool,
- and returns a final response.

It includes both high-level demos and low-level tracing scripts.

## Folder Contents

- `decipher_agents/question_answering_agent/agent.py`
  - Defines the root ADK agent `question_answering_agent`
  - Registers tools: `time_tool` and `weather_tool`
  - Uses model `gemini-2.5-flash`

- `decipher_agents/adk_agent.py`
  - Minimal ADK run
  - Creates an in-memory session
  - Sends one user query and prints final response/session state

- `decipher_agents/adk_agent_tool_selection_steps.py`
  - Step-by-step ADK internals trace
  - Prints tool schema prep, raw LLM input/output chunks, function calls, function responses, and final answer events

- `decipher_agents/adk_agent_tool_selection.py`
  - Thin entry point that runs `adk_agent_tool_selection_steps.main()`

- `decipher_agents/langchain_agent_tool_selection.py`
  - ReAct internals demo in LangChain
  - Shows prompt construction, parser behavior (`AgentAction` / `AgentFinish`), tool execution observations, and executor trajectory comparison

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Install packages:

```bash
pip install google-adk google-genai python-dotenv langchain langchain-openai langchain-community openai
```

## Environment Variables

Create a `.env` file (project root or `decipher_agents` folder) with:

```env
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
```

Notes:

- ADK scripts require `GOOGLE_API_KEY`.
- LangChain OpenAI script requires `OPENAI_API_KEY`.
- Never commit real API keys.

## Run Commands

From `mcp_and_agents` root:

```bash
python decipher_agents/adk_agent.py
```

```bash
python decipher_agents/adk_agent_tool_selection.py
```

```bash
python decipher_agents/adk_agent_tool_selection_steps.py
```

```bash
python decipher_agents/langchain_agent_tool_selection.py
```

## Learning Outcomes

Use these scripts to:

- inspect ADK runtime events around tool selection,
- inspect low-level request/response payloads sent to the model,
- compare ADK tool-calling flow against LangChain ReAct flow,
- and understand where parsing and tool execution happen in each stack.

## Troubleshooting

- If ADK fails: verify `GOOGLE_API_KEY`.
- If LangChain OpenAI fails: verify `OPENAI_API_KEY`.
- If imports fail: install missing dependencies in the active environment.
- If tools are not called: use an explicit prompt such as `What is the current time? Please use a tool.`
