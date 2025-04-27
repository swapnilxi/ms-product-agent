import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import List

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",    
)

# Create the primary agent.
Microsoft_market_agent = AssistantAgent(
    "microsoft_bot",
    model_client=model_client,
    system_message="You are a expert AI assistant and marketer of Microsoft.",
)

Samsung_market_agent = AssistantAgent(
    "samsung_bot",
    model_client=model_client,
    system_message="You are a helpful AI assistant and marketer of Samsung.",
)


# Create the collab agent.
colab_market_agent = AssistantAgent(
    "collaborator",
    model_client=model_client,
    system_message="Think and make a collabrative product of samsung and microsoft in virtual reality and XR domain and prepare a maketing plan in Korea. Respond with 'APPROVE' to when your feedbacks are addressed.",
)

# Define a termination condition that stops the task if the critic approves.
text_termination = TextMentionTermination("APPROVE")

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([Microsoft_market_agent, Samsung_market_agent,colab_market_agent], termination_condition=text_termination)

async def run_marketing_agent(task: List[TextMessage], cancellation_token: CancellationToken):
    await team.reset()

    chat_result = await team.run(
        task=task,
        cancellation_token=cancellation_token,
    )

    # 🖨️ Print the conversation nicely on console
    for message in chat_result.messages:
        print(f"[{message.source}] {message.content}\n")

    return chat_result
    

def main():
    asyncio.run(run_marketing_agent())

if __name__ == "__main__":
    main()
