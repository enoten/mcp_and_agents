"""
ReAct agent internals (langchain_classic `create_react_agent`).

This script runs two paths:
1) A manual thought→action→observation loop that prints the *exact* strings and
   objects at each stage (prompt variables, full prompt text, raw LLM output after
   stop, parsed `AgentAction` / `AgentFinish`, tool observation).
2) The same query through `AgentExecutor` with `return_intermediate_steps=True`
   so you can compare the trajectory to the traced loop.

Pipeline (same as `langchain_classic.agents.react.agent.create_react_agent`):
  RunnablePassthrough.assign(agent_scratchpad=lambda x: format_log_to_str(...))
  | prompt
  | llm.bind(stop=["\\nObservation"])   # default when stop_sequence=True
  | ReActSingleInputOutputParser
"""

from __future__ import annotations

from dotenv import load_dotenv
import langchain_classic.hub as hub
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.agents.format_scratchpad import format_log_to_str
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import Tool
from langchain_core.tools.render import render_text_description
from langchain_openai import ChatOpenAI

load_dotenv()


def get_current_time(*args, **kwargs):
    """Returns the current time in H:MM AM/PM format."""
    import datetime

    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")


def get_current_weather(*args, **kwargs):
    """Returns the current weather in the user's location."""
    return "It is sunny and 70 degrees Fahrenheit."


tools = [
    Tool(
        name="Time",
        func=get_current_time,
        description="Useful for when you need to know the current time",
    ),
    Tool(
        name="Weather",
        func=get_current_weather,
        description=(
            "Useful for when you need to know the current weather in the user's location."
        ),
    ),
]

TOOL_NAMES = ", ".join(t.name for t in tools)
TOOLS_BLOCK = render_text_description(tools)

# ReAct prompt from the hub (same as in course examples).
# https://smith.langchain.com/hub/hwchase17/react
prompt = hub.pull("hwchase17/react").partial(
    tools=TOOLS_BLOCK,
    tool_names=TOOL_NAMES,
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# Mirrors create_react_agent(..., stop_sequence=True)
llm_with_stop = llm.bind(stop=["\nObservation"])
react_parser = ReActSingleInputOutputParser()
prompt_then_llm = prompt | llm_with_stop


def _banner(title: str) -> None:
    line = "=" * len(title)
    print(f"\n{line}\n{title}\n{line}")


def traced_react_run(user_input: str, max_iterations: int = 8) -> None:
    """Step-by-step: scratchpad → formatted prompt → LLM → parse → tool → repeat."""
    _banner("1) Values injected into the ReAct prompt (partial + first step)")
    print("Partial variable `tools` (render_text_description):\n")
    print(TOOLS_BLOCK)
    print("\nPartial variable `tool_names`:\n")
    print(TOOL_NAMES)
    print(
        "\nPer-iteration variables: `input` (your question) and `agent_scratchpad` "
        "(prior Thought/Action/Action Input/Observation steps formatted as text)."
    )

    intermediate_steps: list[tuple[AgentAction, str]] = []
    name_to_tool = {t.name: t for t in tools}
    
    for iteration in range(1, max_iterations + 1):
        _banner(f"2) Iteration {iteration}: build scratchpad and full prompt string")
        scratchpad = format_log_to_str(intermediate_steps)
        print("agent_scratchpad = format_log_to_str(intermediate_steps)")
        print(f"  repr(agent_scratchpad) = {scratchpad!r}\n")

        prompt_vars = {"input": user_input, "agent_scratchpad": scratchpad}
        full_prompt_text = prompt.format(**prompt_vars)
        print("Exact prompt string sent to the chat model (same as prompt.format):\n")
        print(full_prompt_text)

        _banner(f"3) Iteration {iteration}: LLM output (stopped before '\\nObservation')")
        ai_message = prompt_then_llm.invoke(prompt_vars)
        raw_text = (
            ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)
        )
        print("Raw model completion (string passed into ReActSingleInputOutputParser):\n")
        print(raw_text)
        print(
            "\n(With stop=['\\nObservation'], generation stops before the model writes "
            "an Observation line; the executor supplies Observation by running the tool.)"
        )

        _banner(f"4) Iteration {iteration}: parse → AgentAction or AgentFinish")
        print(
            "ReActSingleInputOutputParser.parse(text) looks for either:\n"
            "  - Action: <tool> + Action Input: <input>  → AgentAction\n"
            "  - Final Answer: ...  → AgentFinish\n"
            "(See langchain_classic.agents.output_parsers.react_single_input.)\n"
        )
        parsed = react_parser.parse(raw_text)
        if isinstance(parsed, AgentFinish):
            print("Parsed: AgentFinish")
            print(f"  return_values: {parsed.return_values}")
            print(f"  log (full text): {parsed.log!r}")
            return
        assert isinstance(parsed, AgentAction)
        print("Parsed: AgentAction")
        print(f"  .tool       = {parsed.tool!r}")
        print(f"  .tool_input = {parsed.tool_input!r}")
        print(f"  .log        = {parsed.log!r}")

        _banner(f"5) Iteration {iteration}: execute tool → observation string")
        if parsed.tool not in name_to_tool:
            print(f"Unknown tool {parsed.tool!r} — in AgentExecutor this becomes InvalidTool.")
            return
        tool = name_to_tool[parsed.tool]
        observation = tool.run(parsed.tool_input)
        print(f"observation = tools[{parsed.tool!r}].run({parsed.tool_input!r})")
        print(f"  → {observation!r}")

        intermediate_steps.append((parsed, observation))

    print(f"Stopped after {max_iterations} iterations (max_iterations guard).")


def run_agent_executor_comparison(user_input: str) -> None:
    """Same agent as the course file; returns structured steps for comparison."""
    _banner("6) Same query via AgentExecutor (return_intermediate_steps=True)")
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=hub.pull("hwchase17/react"),
        stop_sequence=True,
    )
    executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True,
    )
    result = executor.invoke({"input": user_input})
    print("Final output:", result.get("output"))
    print("\nIntermediate steps (AgentAction.log + observation per step):")
    for i, (action, obs) in enumerate(result.get("intermediate_steps", []), start=1):
        print(f"\n  Step {i}:")
        print(f"    action.log: {action.log!r}")
        print(f"    observation: {obs!r}")


if __name__ == "__main__":
    user_input = "what is the current weather?"
    user_input = "what is the current time?"

    #traced_react_run(QUERY)
    #run_agent_executor_comparison(QUERY)

    intermediate_steps: list[tuple[AgentAction, str]] = []
    name_to_tool = {t.name: t for t in tools}
    scratchpad = format_log_to_str(intermediate_steps)

    prompt_vars = {"input": user_input, "agent_scratchpad": scratchpad}
    full_prompt_text = prompt.format(**prompt_vars)
    print(">>>>-----")
    print(full_prompt_text)
    print(">>>>-----")


    ai_message = prompt_then_llm.invoke(prompt_vars)
    raw_text = (
            ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)
    )
    print("-----")
    print(raw_text)