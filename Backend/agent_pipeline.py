# agent_pipeline.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

# Import the agents
import researchAgent 
import marketingAgent 

async def research_to_marketing_flow():
    cancellation_token = CancellationToken()

    results = {}

    # Step 1: Run Research Agent
    research_result = await researchAgent.run_research_agent(
        task="Start by discussing the current operations and products of Microsoft and Samsung, then move to their future in XR and where they can collab. The critic will monitor and end when satisfied",
        cancellation_token=cancellation_token,
    )

    # Capture the final message from Research Agent
    research_message = research_result.messages[-1]
    results['research_output'] = research_message.content

    # Step 2: Pass research message to Marketing Agent
    marketing_result = await marketingAgent.run_marketing_agent(
        task=[
            TextMessage(
                content=research_message.content,
                source=research_message.source
            )
        ],
        cancellation_token=cancellation_token,
    )

    # Capture the final marketing message
    marketing_message = marketing_result.messages[-1]
    results['marketing_output'] = marketing_message.content

    return results
if __name__ == "__main__":
    results = asyncio.run(research_to_marketing_flow())
    print("Research Output:", results['research_output'])