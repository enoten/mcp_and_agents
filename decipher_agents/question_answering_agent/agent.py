from datetime import datetime

from google.adk.agents import Agent


def time_tool() -> str:
    """Return the current local date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def weather_tool() -> str:
    """Return a static weather response."""
    return "Weather is fine!"

# Create the root agent
question_answering_agent = Agent(
    name="question_answering_agent",
    model="gemini-2.5-flash",
    description="Question answering agent",
    instruction="""
    You are a helpful assistant that answers questions about the user's preferences.
    You can also use tools to answer time or weather requests:
    - Use `time_tool` for current time.
    - Use `weather_tool` for weather.

    Here is some information about the user:
    Name: 
    {user_name}
    Preferences: 
    {user_preferences}
    """,
    tools=[time_tool, weather_tool],
)
