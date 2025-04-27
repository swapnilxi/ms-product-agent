# !pip install google-genai
import asyncio
import os
from typing import AsyncGenerator,List, Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_core import CancellationToken
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import AssistantMessage, RequestUsage, UserMessage
from google import genai
from google.genai import types
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat


class GeminiAssistantAgent(BaseChatAgent):
    def __init__(
        self,
        name: str,
        description: str = "An agent that provides assistance with ability to use tools.",
        model: str = "gemini-1.5-flash-002",
        api_key: str = "AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",
        system_message: str
        | None = "You are a helpful assistant that can respond to messages. Reply with TERMINATE when the task has been completed.",
    ):
        super().__init__(name=name, description=description)
        self._model_context = UnboundedChatCompletionContext()
        self._model_client = genai.Client(api_key=api_key)
        self._system_message = system_message
        self._model = model

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        final_response = None
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, Response):
                final_response = message

        if final_response is None:
            raise AssertionError("The stream should have returned the final result.")

        return final_response

    async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        # Add messages to the model context
        for msg in messages:
            await self._model_context.add_message(msg.to_model_message())

        # Get conversation history
        history = [
            (msg.source if hasattr(msg, "source") else "system")
            + ": "
            + (msg.content if isinstance(msg.content, str) else "")
            + "\n"
            for msg in await self._model_context.get_messages()
        ]
        # Generate response using Gemini
        response = self._model_client.models.generate_content(
            model=self._model,
            contents=f"History: {history}\nGiven the history, please provide a response",
            config=types.GenerateContentConfig(
                system_instruction=self._system_message,
                temperature=0.3,
            ),
        )

        # Create usage metadata
        usage = RequestUsage(
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
        )

        # Add response to model context
        await self._model_context.add_message(AssistantMessage(content=response.text, source=self.name))

        # Yield the final response
        yield Response(
            chat_message=TextMessage(content=response.text, source=self.name, models_usage=usage),
            inner_messages=[],
        )

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset the assistant by clearing the model context."""
        await self._model_context.clear()
        
        
async def assistant_run() -> None:
    gemini_assistant = GeminiAssistantAgent("gemini_assistant")
    await Console(gemini_assistant.run_stream(task="what is the popular products available at samsung and at microsoft top 3 as per your data not realtime?"))
    
#asyncio.run(assistant_run())

model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key="AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",    
)

primary_agent = AssistantAgent(
    "primary",
    model_client=model_client,
    system_message="You are a helpful AI assistant.",
)

gemini_critic_agent = GeminiAssistantAgent(
    "gemini_critic",
    system_message="Provide constructive feedback. Respond with 'APPROVE' to when your feedbacks are addressed.after 5 messages and name and description of the product in one line",
)

# Define a termination condition that stops the task if the critic approves or after 10 messages.
termination = TextMentionTermination("APPROVE") | MaxMessageTermination(10)

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([primary_agent, gemini_critic_agent], termination_condition=termination)

async def assistant_run() -> None:
    await Console(team.run_stream(task="Let's collaborate on a new product and create a new project of microsoft and samsung"))
    await model_client.close()

asyncio.run(assistant_run())