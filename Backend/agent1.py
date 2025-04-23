import requests
import asyncio
from PIL import Image
from io import BytesIO

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image as AGImage
import os

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY", "AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU")

model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key=api_key,    
)

async def get_product_info(company: str) -> str:
    """Get details about products from a company."""
    # Here you would implement actual API calls to get product info
    # This is just a placeholder implementation
    return f"Products from {company} include ..."  # Replace with actual data

agent = AssistantAgent(
    name="information_agent",
    model_client=model_client,
    tools=[get_product_info],
    system_message="You are a helpful assistant that provides information about company products.",
    reflect_on_tool_use=True,
    model_client_stream=True,
)

# This part is not needed if you're using FastAPI endpoints
# async def main() -> None:
#     await Console(agent.run_stream(task="What are products available at microsoft?"))
#     await model_client.close()

# asyncio.run(main())