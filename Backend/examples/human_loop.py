from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
import asyncio
import os

model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyB0MA1G96Vjp6WeZsoLhF5g96vhk-kb4BA",    
)

assistant = AssistantAgent("assistant", model_client=model_client)
user_proxy = UserProxyAgent("user_proxy", input_func=input)

termination = TextMentionTermination("APPROVE")

team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination,max_turns=7)
task="search a collaborative product of samsung and microsoft in virtual reality and XR domain.ask user if he/she approve the plan or not by saying APPROVE or giving feedback"
async def run_human_loop():
    stream = team.run_stream(task=task)
    await Console(stream)
    await model_client.close()

asyncio.run(run_human_loop())
