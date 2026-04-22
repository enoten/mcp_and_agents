import asyncio
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from question_answering_agent import question_answering_agent

load_dotenv()


async def main() -> None:
    # Create a new session service to store state
    session_service_stateful = InMemorySessionService()

    initial_state = {
        "user_name": "PhiAI User",
        "user_preferences": """
            I like to play Soccer and Tennis.
            My favorite food is Pizza.
            My favorite movie is "13th Floor".
            Loves it when people like and subscribe to YouTube channel.
        """,
    }

    # Create a NEW session
    app_name = "PhiAI Bot"
    user_id = "serg_t"
    session_id = str(uuid.uuid4())
    await session_service_stateful.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state,
    )
    print("CREATED NEW SESSION:")
    print(f"\tSession ID: {session_id}")

    runner = Runner(
        agent=question_answering_agent,
        app_name=app_name,
        session_service=session_service_stateful,
    )

    new_message = types.Content(
        role="user", parts=[types.Part(text="What is the current weather?")]
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                print(f"Final Response: {event.content.parts[0].text}")
    except Exception as exc:
        print(f"Runner execution failed: {exc}")
        print("Check that GOOGLE_API_KEY is set to a valid value in your environment.")

    print("==== Session Event Exploration ====")
    session = await session_service_stateful.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    # Log final Session state
    print("=== Final Session State ===")
    if session:
        for key, value in session.state.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
