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


# Define a model client. You can use other model client that implements
# the `ChatCompletionClient` interface.
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",    
)


# Define a simple function tool that the agent can use.
# For this example, we use a fake weather tool for demonstration purposes.
async def get_product_info(Company: str) -> str:
    """details about Company."""
    return f"The weather in {Company} ."


# Define an AssistantAgent with the model, tool, system message, and reflection enabled.
# The system message instructs the agent via natural language.
agent = AssistantAgent(
    name="information_agent",
    model_client=model_client,
    tools=[ get_product_info],
    system_message="You are a helpful assistant.",
    reflect_on_tool_use=True,
    model_client_stream=True,  # Enable streaming tokens from the model client.
)

#usermessage
text_message = TextMessage(content="Hello, world!", source="User")
pil_image = Image.open(BytesIO(requests.get("https://picsum.photos/300/200").content))
img = AGImage(pil_image)
multi_modal_message = MultiModalMessage(content=["Can you describe the content of this image?", img], source="User")
img

# Run the agent and stream the messages to the console.
async def main() -> None:
    await Console(agent.run_stream(task="What are products available at microsoft?"))
    # Close the connection to the model client.
    await model_client.close()


# NOTE: if running this inside a Python script you'll need to use asyncio.run(main()).
asyncio.run(main())

