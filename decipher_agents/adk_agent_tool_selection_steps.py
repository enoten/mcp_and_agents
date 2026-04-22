import asyncio
import inspect
import json
import uuid
from typing import Any

from dotenv import load_dotenv
from google.adk.models.llm_request import LlmRequest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from question_answering_agent import question_answering_agent

load_dotenv()


def _print_flow_guide() -> None:
    """Explain ADK tool selection flow before execution starts."""
    print("=== How ADK Selects a Tool (Step-by-Step) ===")
    print("1) Register tools on the Agent (done in question_answering_agent).")
    print("2) Build user message and call Runner.run_async(...).")
    print("3) ADK sends tool schemas + context to the model.")
    print("4) Model decides whether to call a tool.")
    print("5) If yes, event contains part.function_call (tool name + args).")
    print("6) ADK executes that tool and returns part.function_response.")
    print("7) Model uses tool result to produce final response.")


def _print_step_header(step_no: int, title: str) -> None:
    print()
    print(f"===== STEP {step_no}) {title} =====")


def _print_call_and_output(call_expr: str, output: Any) -> None:
    print(f"Code call : {call_expr}")
    print(f"Output    : {output}")


def _make_after_model_debug_callback() -> Any:
    """Print raw llm_response chunks yielded by generate_content_async."""
    chunk_counter = {"value": 0}

    def _after_model_callback(callback_context: Any, llm_response: Any) -> None:
        del callback_context  # Not used in this demo, but part of callback signature.
        chunk_counter["value"] += 1
        print()
        print("----- RAW LLM OUTPUT CHUNK -----")
        _print_call_and_output(
            "responses_generator = llm.generate_content_async(llm_request, stream=...)",
            f"chunk #{chunk_counter['value']}",
        )
        if hasattr(llm_response, "model_dump"):
            print(json.dumps(llm_response.model_dump(mode="json", exclude_none=True), indent=2, default=str))
        else:
            print(llm_response)
        print("----- END RAW LLM OUTPUT CHUNK -----")
        return None

    return _after_model_callback


def _make_before_model_debug_callback() -> Any:
    """Print the exact llm_request before generate_content_async is called."""

    def _before_model_callback(callback_context: Any, llm_request: Any) -> None:
        del callback_context  # Not used in this demo, but part of callback signature.
        print()
        print("----- RAW LLM INPUT (BEFORE MODEL CALL) -----")
        _print_call_and_output(
            "before_model_callback(callback_context, llm_request)",
            "About to call: responses_generator = llm.generate_content_async(llm_request, stream=...)",
        )
        if hasattr(llm_request, "model_dump"):
            print(json.dumps(llm_request.model_dump(mode="json", exclude_none=True), indent=2, default=str))
        else:
            print(llm_request)
        print("----- END RAW LLM INPUT -----")
        return None

    return _before_model_callback


def _print_content_parts(content: Any, step_index: int) -> None:
    """Print useful tool-selection details from event content parts."""
    if not content or not getattr(content, "parts", None):
        return

    for part in content.parts:
        text = getattr(part, "text", None)
        if text:
            print(f"[Runtime Step {step_index}] Model message: {text}")

        function_call = getattr(part, "function_call", None)
        if function_call:
            call_name = getattr(function_call, "name", "unknown_tool")
            call_args = getattr(function_call, "args", {})
            print(f"[Runtime Step {step_index}] PHASE 4/5 -> Tool selected: {call_name}")
            print(f"[Runtime Step {step_index}] Tool args: {call_args}")

        function_response = getattr(part, "function_response", None)
        if function_response:
            response_name = getattr(function_response, "name", "unknown_tool")
            response_value = getattr(function_response, "response", {})
            print(
                f"[Runtime Step {step_index}] PHASE 6 -> Tool response from {response_name}: {response_value}"
            )


def _llm_request_to_printable_dict(llm_request: LlmRequest) -> dict[str, Any]:
    """Mirror of what gets sent on the wire: model + contents + config.tools.

    tools_dict is ADK-only (name -> BaseTool) for dispatch after function_call;
    it is not the HTTP body field list (see LlmRequest in google.adk.models).
    """
    config_dump: Any = None
    if llm_request.config is not None:
        config_dump = llm_request.config.model_dump(mode="json", exclude_none=True)
    return {
        "model": llm_request.model,
        "contents": [c.model_dump(mode="json", exclude_none=True) for c in llm_request.contents],
        "config": config_dump,
        "tools_dict (local registry; maps function_call.name -> BaseTool)": {
            name: type(tool).__name__ for name, tool in llm_request.tools_dict.items()
        },
    }


async def _print_llm_request_append_tools_demo() -> None:
    """Same path as LlmRequest.append_tools in ADK: declarations + tools_dict."""
    resolved_tools = await question_answering_agent.canonical_tools(None)
    llm_request = LlmRequest(model=question_answering_agent.model)
    print(f">>>>>>>>>>>>>>>>>> {llm_request}")
    llm_request.append_tools(resolved_tools)
    print(f">>>>>>>>>>>>>>>>>> {llm_request}")
    _print_call_and_output(
        "LlmRequest(model=...); llm_request.append_tools(await agent.canonical_tools(None))",
        "(see JSON below: config.tools.function_declarations + tools_dict keys)",
    )
    printable = _llm_request_to_printable_dict(llm_request)
    print("JSON (default=str for any non-serializable nested values):")
    print(json.dumps(printable, indent=2, default=str))


def _build_tool_schema_snapshot(tools: list[Any]) -> list[dict[str, Any]]:
    """Build a human-readable schema snapshot for each registered tool."""
    snapshot: list[dict[str, Any]] = []
    for tool in tools:
        signature = str(inspect.signature(tool))
        snapshot.append(
            {
                "name": getattr(tool, "__name__", "unknown_tool"),
                "signature": f"{getattr(tool, '__name__', 'tool')}{signature}",
                "doc": (inspect.getdoc(tool) or "").strip(),
            }
        )
    return snapshot


async def main() -> None:
    _print_flow_guide()

    session_service_stateful = InMemorySessionService()

    initial_state = {
        "user_name": "PhiAI User",
        "user_preferences": """
            I like to play Soccer and Tennis.
            My favorite food is Pizza.
            My favorite movie is "13th Floor".
        """,
    }

    app_name = "PhiAI Tool Selection Demo"
    user_id = "serg_t"
    session_id = str(uuid.uuid4())

    await session_service_stateful.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state,
    )

    #_print_step_header(1, "Agent already has tools registered")
    tool_names = [tool.__name__ for tool in question_answering_agent.tools]
    #_print_call_and_output("question_answering_agent.tools", tool_names)

    #_print_step_header(2, "Build user message + create runner")
    original_before_model_callback = question_answering_agent.before_model_callback
    original_after_model_callback = question_answering_agent.after_model_callback
    question_answering_agent.before_model_callback = _make_before_model_debug_callback()
    question_answering_agent.after_model_callback = _make_after_model_debug_callback()
    #_print_call_and_output(
    #    "question_answering_agent.before_model_callback = _make_before_model_debug_callback()",
    #    "Enabled debug print for full llm_request before generate_content_async.",
    #)
    #_print_call_and_output(
    #    "question_answering_agent.after_model_callback = _make_after_model_debug_callback()",
    #    "Enabled debug print for each raw llm_response chunk from generate_content_async.",
    #)
    runner = Runner(
        agent=question_answering_agent,
        app_name=app_name,
        session_service=session_service_stateful,
    )
    new_message = types.Content(
        role="user",
        parts=[types.Part(text="What is the current time? Please use a tool.")],
    )
    # _print_call_and_output(
    #     "Runner(...) and types.Content(role='user', parts=[...])",
    #     {"app_name": app_name, "session_id": session_id, "user_message": new_message.parts[0].text},
    # )

    # _print_step_header(3, "ADK prepares model input (tools + context)")
    tool_schemas_snapshot = _build_tool_schema_snapshot(question_answering_agent.tools)
    session = await session_service_stateful.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    session_state_for_model = session.state if session else {}
    # _print_call_and_output(
    #     "_build_tool_schema_snapshot(question_answering_agent.tools)",
    #     tool_schemas_snapshot,
    # )
    # _print_call_and_output(
    #     "session_service_stateful.get_session(...).state",
    #     session_state_for_model,
    # )
    # _print_call_and_output(
    #     "runner.run_async(user_id=..., session_id=..., new_message=...)",
    #     "Streaming starts with the above tool schemas + session state.",
    # )

    # print()
    # print("--- LlmRequest.append_tools (google.adk.models.llm_request) ---")
    # print(
    #     "This builds the same structure ADK uses: "
    #     "tool._get_declaration() -> function_declarations on config.tools, "
    #     "and tools_dict[tool.name] = tool for execution routing."
    # )
    await _print_llm_request_append_tools_demo()

    # print()
    # print("=== Runtime Trace ===")
    # print(f"Session ID: {session_id}")

    step_index = 1
    saw_function_call = False
    saw_function_response = False
    saw_final_response = False
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            author = getattr(event, "author", "unknown")
            print(f"\n--- Runtime Step {step_index} | Author: {author} ---")
            content = getattr(event, "content", None)
            _print_content_parts(content, step_index)

            if content and getattr(content, "parts", None):
                for part in content.parts:
                    if getattr(part, "function_call", None):
                        if not saw_function_call:
                            _print_step_header(4, "Model decides to use a tool")
                            _print_call_and_output(
                                "event.content.parts[i].function_call",
                                {
                                    "name": part.function_call.name,
                                    "args": getattr(part.function_call, "args", {}),
                                },
                            )
                            _print_step_header(5, "Chosen tool + arguments are emitted")
                            _print_call_and_output(
                                "part.function_call.name / part.function_call.args",
                                f"{part.function_call.name} / {getattr(part.function_call, 'args', {})}",
                            )
                        saw_function_call = True

                    if getattr(part, "function_response", None):
                        if not saw_function_response:
                            _print_step_header(6, "ADK executes tool and returns output")
                            _print_call_and_output(
                                "event.content.parts[i].function_response",
                                {
                                    "name": part.function_response.name,
                                    "response": getattr(part.function_response, "response", {}),
                                },
                            )
                        saw_function_response = True

            if event.is_final_response():
                if not saw_final_response:
                    _print_step_header(7, "Model returns final answer using tool output")
                    _print_call_and_output(
                        "event.is_final_response()",
                        "True",
                    )
                saw_final_response = True
                print(f"[Runtime Step {step_index}] PHASE 7 -> Final response reached.")

            step_index += 1
    except Exception as exc:
        print(f"Runner execution failed: {exc}")
        print("Check that GOOGLE_API_KEY is set to a valid value in your environment.")
    finally:
        question_answering_agent.before_model_callback = original_before_model_callback
        question_answering_agent.after_model_callback = original_after_model_callback


if __name__ == "__main__":
    asyncio.run(main())
