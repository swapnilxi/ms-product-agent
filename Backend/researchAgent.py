#marketing research agent
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console
from typing import List, Optional
from dotenv import load_dotenv
import os

load_dotenv()


# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyB0MA1G96Vjp6WeZsoLhF5g96vhk-kb4BA",    
)
# Define Research Agent 1: Current business research
research_agent_current = AssistantAgent(
    name="research_agent_current",
    model_client=model_client,
    system_message="You are a research assistant. Provide detailed and up-to-date information about the CURRENT business operations of Microsoft and Samsung.",
)

# Define Research Agent 2: Future XR research
research_agent_future = AssistantAgent(
    name="research_agent_future",
    model_client=model_client,
    system_message="You are a research assistant. Explore and discuss the FUTURE plans of Microsoft and Samsung, especially in XR (Extended Reality) technologies.",
)

# Define Critic/Review Agent
critic_agent = AssistantAgent(
    name="critic_agent",
    model_client=model_client,
    system_message=(
        "You are a review agent. Listen to the discussion between research agents. "
        "If you feel you have gathered ENOUGH DATA and NUMBERS, at least 3 for a report from both of the agent, respond with 'ENOUGH INFO'."
    ),
)

# Create a termination condition based on critic's approval
termination_condition = TextMentionTermination(text="ENOUGH INFO")

# Setup a group chat between all agents
team = RoundRobinGroupChat(
    [research_agent_current, research_agent_future, critic_agent],
    termination_condition=termination_condition,
)

# Default task for standalone
def get_default_task():
    return "Let's research for making a marketing plan for the new XR/VR product between Microsoft and Samsung. after researching the market and global product condition in Korea."

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

    final_task = (
        f"Let's research for creating a marketing plan for a new collabrative product between {company1} and {company2} and make sure to consider their current relation and future potential and market in geographical condtion which user will be mentioning in below instruction.\n"
        f"\n--- User Instruction ---\n{user_input.strip()}"
    )

    if task:
        final_task += f"\n\n--- Context from Previous Agent(s) ---\n{task.strip()}"

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