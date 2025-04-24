import os
import json
import logging
import asyncio
import traceback
from io import BytesIO
from typing import Dict, Any, Optional, List, Union

import requests
from PIL import Image

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_core import Image as AGImage


from fastapi import FastAPI
from mangum import Mangum


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variable
API_KEY = os.getenv("API_KEY", "AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU")

# Initialize model client
def get_model_client(model_name: str = "gemini-1.5-flash-8b") -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(model=model_name, api_key=API_KEY)

# Define function tool
async def get_product_info(company: str) -> str:
    return f"The products available at {company} include cloud computing services, productivity software, and hardware devices."

# Create the agent
def build_agent() -> AssistantAgent:
    return AssistantAgent(
        name="information_agent",
        model_client=get_model_client(),
        tools=[get_product_info],
        system_message="You are a helpful assistant.",
        reflect_on_tool_use=True,
        model_client_stream=True
    )

# Process image
async def fetch_image(url: str) -> Optional[AGImage]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return AGImage(Image.open(BytesIO(response.content)))
    except Exception as e:
        logger.error(f"Image fetch error: {e}")
        return None

# Create message
async def build_message(msg_type: str, content: Union[str, List], image_url: Optional[str] = None):
    try:
        if msg_type.lower() == "text":
            return TextMessage(content=content, source="User")
        elif msg_type.lower() == "multimodal" and image_url:
            img = await fetch_image(image_url)
            if img:
                return MultiModalMessage(content=[content, img], source="User")
    except Exception as e:
        logger.error(f"Message creation error: {e}")
    return None

# Main execution function
async def run_agent(task: str, msg_type: str = "text", image_url: Optional[str] = None) -> Dict[str, Any]:
    agent = build_agent()
    responses = []

    class Collector:
        async def __call__(self, agent_response):
            responses.append(str(agent_response))

    try:
        await agent.run_stream(task=task, stream_handler=Collector())
        await agent.model_client.close()
        return {
            "statusCode": 200,
            "body": json.dumps({
                "responses": responses,
                "message": "Agent execution completed."
            })
        }
    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Agent execution failed."
            })
        }

# Lambda handler
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        task = event.get("task", "What are products available at Microsoft?")
        msg_type = event.get("message_type", "text")
        image_url = event.get("image_url")
        logger.info(f"Lambda called with task: {task}")
        return asyncio.run(run_agent(task, msg_type, image_url))
    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Lambda execution failed."
            })
        }

# Local testing
if __name__ == "__main__":
    test_event = {
        "task": "What are products available at Microsoft?",
        "message_type": "text"
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
