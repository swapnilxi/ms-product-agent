import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import List, Optional
from dotenv import load_dotenv
import os

load_dotenv()


# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key=os.getenv("GEMINI_API_KEY"),    
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
    system_message="Think and make a collabrative product of samsung and microsoft in virtual reality and XR domain and prepare a maketing plan in Korea. Respond with capital letter approve when aleast agent has spoken twice and you find good data from them",
)

# Define a termination condition that stops the task if the critic approves.
termination_condition = TextMentionTermination("APPROVE")


# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([Microsoft_market_agent, Samsung_market_agent,colab_market_agent], termination_condition=termination_condition)


# Default task for standalone
def get_default_task():
    return "Let's prepare a marketing plan on the new XR/VR product between Microsoft and Samsung. and also prepare a marketing plan in Korea."

# Shared result class
class ChatResult:
    def __init__(self, messages: List[TextMessage]):
        self.messages = messages

# Unified runner
async def run_agent(task=None, cancellation_token=None):
    await team.reset()

    task = task or get_default_task()

    # Collect messages during stream
    messages = []
    async for message in team.run_stream(
        task=task,
        cancellation_token=cancellation_token
    ):
        if isinstance(message, TaskResult):
            print(f"✅ Task completed: {message.stop_reason}\n")
        else:
            print(f"[{message.source}] {message.content}\n")
            messages.append(message)

    return ChatResult(messages)
    
async def run_agent_post(company1: str, company2: str, user_input: Optional[str] = None, task: Optional[str] = None):
    await team.reset()

    final_task = (
        f"Prepare a collaborative marketing plan for an XR/VR product between {company1} and {company2}, focused on the Korean market.\n"
        f"\n--- User Instruction ---\n{user_input.strip()}"
    )

    if task:
        final_task += f"\n\n--- Context from Previous Agent(s) ---\n{task.strip()}"

    messages = []
    async for message in team.run_stream(task=final_task, cancellation_token=None):
        if isinstance(message, TaskResult):
            print(f"✅ Task completed: {message.stop_reason}\n")
        else:
            print(f"[{message.source}] {message.content}\n")
            messages.append(message)

    return ChatResult(messages)

def main():
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()
