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

# Create the first marketing agent.
Microsoft_product_agent = AssistantAgent(
    "microsoft_product_bot",
    model_client=model_client,
    system_message="You are a expert executive of  Microsoft. having idea and description of microsoft products offering.",
)

# Create the second marketing agent.
Samsung_product_agent = AssistantAgent(
    "samsung_product_bot",
    model_client=model_client,
    system_message="You are a expert executive of  Microsoft. having idea and description of samsung products offering.",
)


# Create the collab agent.
colab_agent = AssistantAgent(
    "collaborator",
    model_client=model_client,
    system_message="Think and make a collabrative product of samsung and microsoft in xr and virtual reality. Respond with 'APPROVE' to when your feedbacks are addressed.",
)

# Define a termination condition that stops the task if the critic approves.
text_termination = TextMentionTermination("APPROVE")

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([Microsoft_product_agent, Samsung_product_agent,colab_agent], termination_condition=text_termination)

async def run_product_agent():
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
    asyncio.run(run_product_agent())

if __name__ == "__main__":
    main()
