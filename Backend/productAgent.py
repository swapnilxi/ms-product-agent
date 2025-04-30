import asyncio

from autogen_agentchat.agents import AssistantAgent
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
# model_client = OpenAIChatCompletionClient(
#     model="gpt-4o",
#     api_key=os.getenv("OPENAI_API_KEY"),
# )

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
    system_message="Think and make a collabrative product of samsung and microsoft in xr and virtual reality. only respond with approve when each agent has spoken twice and you are satified with the product. then said approve in capital letters ",
)

# Define a termination condition that stops the task if the critic approves.
termination_condition = TextMentionTermination("APPROVE")

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([Microsoft_product_agent, Samsung_product_agent,colab_agent], termination_condition=termination_condition)

# Default task for standalone
def get_default_task():
    return "Let's collaborate on a new XR/VR product between Microsoft and Samsung."

# Unified runner
async def run_agent(task=None, cancellation_token=None):
    await team.reset()

    task = task or get_default_task()

    chat_result = await team.run(
        task=task,
        cancellation_token=cancellation_token
    )

    for message in chat_result.messages:
        print(f"[{message.source}] {message.content}\n")

    return chat_result

async def run_agent_post(company1: str, company2: str, user_input: Optional[str] = None, task: str = None):
    await team.reset()

    # Combine both the user's instruction and previous task context if provided
    final_task = (
        f"Think and make a collabrative product between {company1} and {company2}\n\n"
        f"User Instruction: {user_input.strip()}\n"
    )
    
    if task:
        final_task += f"\nContext from previous agent(s):\n{task.strip()}"

    chat_result = await team.run(
        task=final_task,
        cancellation_token=None
    )

    for message in chat_result.messages:
        print(f"[{message.source}] {message.content}\n")

    return chat_result


def main():
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()
