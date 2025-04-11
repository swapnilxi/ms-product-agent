import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import SelectorGroupChat

# Create an OpenAI model client with Gemini settings
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key= os.environ.get("API_KEY"),  # Replace with your actual API key
)

# Create the agents with modified prompts to handle the feedback loop
microsoft_expert = AssistantAgent(
    name="MicrosoftExpert",
    system_message="""You are an expert on Microsoft's products, services, market position, and business strategies.
    When asked about company products, provide a detailed analysis of Microsoft's latest products or initiatives.
    After your analysis, pass the conversation to the Samsung expert.""",
    model_client=model_client
)

samsung_expert = AssistantAgent(
    name="SamsungExpert",
    system_message="""You are an expert on Samsung's products, services, market position, and business strategies.
    When the Microsoft expert passes the conversation to you, provide a detailed analysis of Samsung's latest products or initiatives.
    After your analysis, pass the conversation to the Innovation agent.""",
    model_client=model_client
)

innovation_agent = AssistantAgent(
    name="InnovationAgent",
    system_message="""You identify innovative collaborative projects between Microsoft and Samsung, focusing on unique selling points and requirements.
    Based on the information from both company experts, propose 2-3 innovative collaboration ideas.

    IMPORTANT: Check if the Review agent has previously DISAPPROVED an idea. If so, propose completely new ideas.

    After presenting your ideas, pass the conversation to the Marketing Research agent.""",
    model_client=model_client
)

marketing_research = AssistantAgent(
    name="MarketingResearchAgent",
    system_message="""You analyze sales data country-wise and identify market trends for Microsoft-Samsung collaborations.
    Based on the innovative ideas proposed, identify the top markets globally that would be receptive to these collaborations.

    Only respond if the Innovation agent has successfully proposed ideas.

    After your market analysis, pass the conversation to the Marketing Plan agent.""",
    model_client=model_client
)

marketing_plan = AssistantAgent(
    name="MarketingPlanAgent",
    system_message="""You develop detailed marketing plans for the top 3 performing countries.
    Based on the market research, create a concise marketing strategy for the top markets identified.

    Only respond if the Marketing Research agent has successfully identified markets.

    After presenting your marketing plan, pass the conversation to the Review agent.""",
    model_client=model_client
)

review_agent = AssistantAgent(
    name="ReviewAgent",
    system_message="""You review and summarize the outputs from other agents, creating concise reports.
    Create an executive summary of all the insights and plans shared by previous agents.

    After your summary, you must decide to either:
    1. ACCEPT the plan: End your message with "This plan is ACCEPTED." and pass to the Dashboard agent
    2. REJECT the plan: End your message with "This plan is REJECTED." and pass back to the Innovation agent

    IMPORTANT: When rejecting, NEVER use the word "APPROVE" anywhere in your message.
    
    If you REJECT, explicitly ask the Innovation agent to propose new ideas and all other agents should wait until new ideas are proposed.
    If you ACCEPT, the Dashboard agent should proceed with creating the dashboard.""",
    model_client=model_client
)

dashboard_agent = AssistantAgent(
    name="DashboardAgent",
    system_message="""You prepare dashboard data for higher management and handle customer support inquiries.

    IMPORTANT: Only respond if the Review agent has ACCEPTED the plan. If the review is not yet accepted, simply state "Waiting for plan acceptance" and pass back to the Review agent.

    Based on all the information shared, provide key metrics and dashboard elements that would be useful for tracking the success of these initiatives.
    You are the final agent in this conversation. After providing your dashboard recommendations, end your message with the exact phrase: "This concludes our analysis. APPROVE"

    If you see that a previous cycle was REJECTED, wait for a new accepted plan before creating your dashboard.""",
    model_client=model_client
)

# Define termination condition
approval_termination = TextMentionTermination("This concludes our analysis. APPROVE")

# Create team with all agents in a specific order
team = SelectorGroupChat(
    [
        microsoft_expert,
        samsung_expert,
        innovation_agent,
        marketing_research,
        marketing_plan,
        review_agent,
        dashboard_agent
    ],
    termination_condition=approval_termination,
    model_client=model_client
)


async def run_team_chat():
    # Create cancellation token
    cancellation_token = CancellationToken()

    # Reset team for new task
    await team.reset()

    # Set clear initial task with instructions for flow
    task = """
    What are the latest products or innovations from Microsoft and Samsung, and how might these companies collaborate?
    Please analyze this in a structured way where each agent builds on the previous agent's contributions.

    The process should include:
    1. Microsoft and Samsung experts providing product information
    2. Innovation Agent proposing collaboration ideas
    3. Marketing Research identifying target markets
    4. Marketing Plan developing strategies
    5. Review Agent approving or disapproving the plan
    6. Dashboard Agent creating final metrics (only if approved)

    If the Review Agent disapproves, all agents should understand that we need to restart from the Innovation Agent to generate new ideas.
    The process continues until a plan is approved and the Dashboard agent finalizes the analysis.
    """

    # Run team chat
    async for message in team.run_stream(
            task=task,
            cancellation_token=cancellation_token
    ):
        print(message)

        # Optional: Add a small delay between agent responses for readability
        await asyncio.sleep(10)


# Run the async function
if __name__ == "__main__":
    asyncio.run(run_team_chat())