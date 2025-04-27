import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",    
)

# Create the primary agent.
Microsoft_agent = AssistantAgent(
    "microsoft_bot",
    model_client=model_client,
    system_message="You are a helpful AI assistant of Microsoft.",
)

Samsung_agent = AssistantAgent(
    "samsung_bot",
    model_client=model_client,
    system_message="You are a helpful AI assistant of Samsung.",
)


# Create the critic agent.
colab_agent = AssistantAgent(
    "collaborator",
    model_client=model_client,
    system_message="Think and make a collabrative product of samsung and microsoft. Respond with 'APPROVE' to when your feedbacks are addressed.",
)

# Define a termination condition that stops the task if the critic approves.
text_termination = TextMentionTermination("APPROVE")

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([Microsoft_agent, Samsung_agent,colab_agent], termination_condition=text_termination)

async def run_marketing_agent():
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Reset the team for a new task
    await team.reset()
    
    # Run the team chat and process messages
    async for message in team.run_stream(
        task="Let's collaborate on a new product.",
        cancellation_token=cancellation_token
    ):
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
        else:
            print(message)

def main():
    asyncio.run(run_marketing_agent())

if __name__ == "__main__":
    main()
