
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage, TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from dotenv import load_dotenv
import os

load_dotenv()


# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key=os.getenv("GEMINI_API_KEY"),
)

fetch_mcp_server = StdioServerParams(command="uvx", args=["mcp-server-fetch"])
#tools = mcp_server_tools(fetch_mcp_server)

async def web_search_func(query: str) -> str:
    """Find information on the web"""
    return "AutoGen is a programming framework for building multi-agent applications."

tools=""
async def initialize_agent() -> AssistantAgent:
    # Await the mcp_server_tools coroutine to get the tools
    tools = await mcp_server_tools(fetch_mcp_server)

    # Initialize the MCP agent with the correct tools
    agent = AssistantAgent(
        name="MCPfetcher",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True,
    )
    return agent






# Define a tool that searches the web for information.
async def web_search(query: str) -> str:
    """Find information on the web"""
    return "The web search results for {query}."
web_search_function_tool = FunctionTool(web_search_func, description="Find information on the web")
# The schema is provided to the model during AssistantAgent's on_messages call.
web_search_function_tool.schema


#Agent
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    tools=[web_search],
    system_message="Use tools to solve tasks.",
)

# Initialize the MCP agent with the correct tools
agent = AssistantAgent(
    name="MCPfetcher", 
    model_client=model_client, 
    tools=tools, 
    reflect_on_tool_use=True
    )  # type: ignore


async def assistant_run() -> None:
    response = await agent.on_messages(
        [TextMessage(content="Find information on samsung products and smart tv", source="user")],
        cancellation_token=CancellationToken(),
    )
    #print(response)
    print(response.inner_messages)
    print(response.chat_message)
    
async def assistant_run_stream() -> None:
    await Console(
            agent.on_messages_stream(
                [TextMessage(content="Find information on samsung products of smart tv", source="user")],
                cancellation_token=CancellationToken(),
            ),
            output_stats=True,  # Enable stats printing.
        )
    
async def assistant_run_mcp() -> None:
    # Initialize the agent
    agent = await initialize_agent()

    # Run the task and get the result
    result = await agent.run(task="Summarize the content of https://en.wikipedia.org/wiki/Seattle")

    # Ensure the last message is a TextMessage
    assert isinstance(result.messages[-1], TextMessage)

    # Print the content of the last message
    print(result.messages[-1].content)    

    
# Use asyncio.run(assistant_run()) when running in a script.
#asyncio.run(assistant_run())
asyncio.run(assistant_run())

