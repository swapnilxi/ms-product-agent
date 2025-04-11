import asyncio
from utils.scraper import (
    get_product_data
)
import os
from dotenv import load_dotenv
load_dotenv()
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import SelectorGroupChat
from utils.pdf_generator import capture_and_save_dashboard_output

# Create an OpenAI model client with Gemini settings
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash-8b",
    api_key= os.environ.get("API_KEY"),  # Replace with your actual API key
    temperature=0.2,  # Lower temperature for more focused responses
    max_tokens=1500,  # Limit token length to avoid truncation
)

# Response format instruction to be added to all agents
FORMAT_INSTRUCTION = """
IMPORTANT FORMAT INSTRUCTION:
1. Your response MUST be clear, concise, and focused only on your specific role.
2. NEVER perform another agent's job - stay strictly within your assigned role.
3. ALWAYS end your message by explicitly passing the conversation to the next agent by name.
4. Format your message with clear headings and bullet points for easy readability.
"""

# Create the agents with modified prompts to handle the feedback loop
microsoft_expert = AssistantAgent(
    name="MicrosoftExpert",
    system_message=f"""You are an expert EXCLUSIVELY on Microsoft's products, services, market position, and business strategies.

    Your ONLY job is to provide a detailed analysis of Microsoft's latest products or initiatives.
    
    {FORMAT_INSTRUCTION}
    
    CRITICAL: You must ONLY discuss Microsoft products and services. DO NOT mention Samsung or any Samsung products.
    DO NOT propose any collaboration ideas - that is another agent's job.
    
    After your analysis, end with the phrase: "I now pass the conversation to the Samsung expert."
    """,
    model_client=model_client,
    tools=[]
)

samsung_expert = AssistantAgent(
    name="SamsungExpert",
    system_message=f"""You are an expert EXCLUSIVELY on Samsung's products, services, market position, and business strategies.

    Your ONLY job is to provide a detailed analysis of Samsung's latest products or initiatives.
    
    {FORMAT_INSTRUCTION}
    
    CRITICAL: You must ONLY discuss Samsung products and services. DO NOT mention Microsoft products or propose any collaboration ideas.
    
    After your analysis, end with the phrase: "I now pass the conversation to the Innovation agent."
    """,
    model_client=model_client,
    tools=[]
)

innovation_agent = AssistantAgent(
    name="InnovationAgent",
    system_message=f"""You identify innovative collaborative projects between Microsoft and Samsung, focusing on unique selling points and requirements.
    
    Based on the information from both company experts, propose 2-3 innovative collaboration ideas.
    
    {FORMAT_INSTRUCTION}

    IMPORTANT: Check if the Review agent has previously DISAPPROVED an idea. If so, propose completely new ideas.
    
    Format your ideas with clear headings and bullet points.

    After presenting your ideas, end with the phrase: "I now pass the conversation to the Marketing Research agent."
    """,
    model_client=model_client
)

marketing_research = AssistantAgent(
    name="MarketingResearchAgent",
    system_message=f"""You analyze sales data country-wise and identify market trends for Microsoft-Samsung collaborations.
    
    Based on the innovative ideas proposed, identify the top markets globally that would be receptive to these collaborations.
    
    {FORMAT_INSTRUCTION}

    Only respond if the Innovation agent has successfully proposed ideas.
    
    Format your market analysis with clear headings, tables, and bullet points.

    After your market analysis, end with the phrase: "I now pass the conversation to the Marketing Plan agent."
    """,
    model_client=model_client
)

marketing_plan = AssistantAgent(
    name="MarketingPlanAgent",
    system_message=f"""You develop detailed marketing plans for the top 3 performing countries.
    
    Based on the market research, create a concise marketing strategy for the top markets identified.
    
    {FORMAT_INSTRUCTION}

    Only respond if the Marketing Research agent has successfully identified markets.
    
    Format your marketing plan with clear headings, bullet points, and timelines.

    After presenting your marketing plan, end with the phrase: "I now pass the conversation to the Review agent."
    """,
    model_client=model_client
)

review_agent = AssistantAgent(
    name="ReviewAgent",
    system_message=f"""You review and summarize the outputs from other agents, creating concise reports.
    
    Create an executive summary of all the insights and plans shared by previous agents.
    
    {FORMAT_INSTRUCTION}

    After your summary, you must decide to either:
    1. ACCEPT the plan: End your message with "This plan is ACCEPTED. I now pass the conversation to the Dashboard agent."
    2. REJECT the plan: End your message with "This plan is REJECTED. I now pass the conversation back to the Innovation agent."

    IMPORTANT: When rejecting, NEVER use the word "APPROVE" anywhere in your message.
    
    If you REJECT, explicitly ask the Innovation agent to propose new ideas and all other agents should wait until new ideas are proposed.
    If you ACCEPT, the Dashboard agent should proceed with creating the dashboard.
    """,
    model_client=model_client
)

dashboard_agent = AssistantAgent(
    name="DashboardAgent",
    system_message=f"""You prepare dashboard data for higher management and handle customer support inquiries.

    IMPORTANT: Only respond if the Review agent has ACCEPTED the plan. If the review is not yet accepted, simply state "Waiting for plan acceptance" and pass back to the Review agent.

    Based on all the information shared, provide key metrics and dashboard elements that would be useful for tracking the success of these initiatives.
    
    {FORMAT_INSTRUCTION}
    
    Format your dashboard recommendations in clear sections with:
    - Key Performance Indicators (KPIs)
    - Visualization recommendations
    - Data sources
    - Update frequency
    
    You are the final agent in this conversation. After providing your dashboard recommendations, end your message with the exact phrase: "This concludes our analysis. APPROVE"

    If you see that a previous cycle was REJECTED, wait for a new accepted plan before creating your dashboard.
    """,
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
    model_client=model_client,
      # Limit maximum rounds to prevent infinite loops
)


async def run_team_chat():
    # Create cancellation token
    cancellation_token = CancellationToken()

    # Reset team for new task
    await team.reset()

    # Store all messages and specifically track the final message
    all_messages = []
    final_message = None

    # Set clear initial task with explicit flow instructions
    task = """
    What are the latest products or innovations from Microsoft and Samsung, and how might these companies collaborate?
    
    IMPORTANT PROCESS INSTRUCTIONS:
    1. First, the Microsoft Expert will ONLY provide information about Microsoft products and innovations.
    2. Then, the Samsung Expert will ONLY provide information about Samsung products and innovations.
    3. Next, the Innovation Agent will propose collaboration ideas based on this information.
    4. The Marketing Research Agent will then identify target markets for these ideas.
    5. The Marketing Plan Agent will develop strategies for the top markets.
    6. The Review Agent will evaluate the overall plan and either accept or reject it.
    7. Finally, if accepted, the Dashboard Agent will create metrics for tracking success.
    
    Each agent MUST stay within their assigned role and pass to the next agent when finished.
    """

    # Run team chat
    try:
        async for message in team.run_stream(
                task=task, 
                cancellation_token=cancellation_token
        ):
            print(message)
            all_messages.append(message)
            final_message = message  # Keep track of the final message
            
            # Optional: Add a small delay between agent responses for readability
            await asyncio.sleep(10)
        
        # After chat completes, save the dashboard output to PDF
        pdf_path = capture_and_save_dashboard_output(all_messages)
        
        # If normal extraction fails, try with just the final message
        if not pdf_path and final_message:
            pdf_path = capture_and_save_dashboard_output([final_message])
            
        if pdf_path:
            print(f"\nDashboard successfully saved to PDF: {pdf_path}")
        else:
            print("\nNo dashboard output was saved to PDF through standard methods.")
            
            # Create a manual extraction as a last resort
            try:
                if final_message:
                    from utils.pdf_generator import save_to_pdf
                    
                    # Create reports directory if it doesn't exist
                    os.makedirs('reports', exist_ok=True)
                    
                    # Extract content from the final message
                    content = ""
                    if hasattr(final_message, 'content'):
                        content = final_message.content
                    elif isinstance(final_message, dict):
                        content = final_message.get('content', '')
                    elif isinstance(final_message, str):
                        content = final_message
                        
                    # Clean up the content
                    if 'DashboardAgent' in content:
                        start_idx = content.find('DashboardAgent')
                        if start_idx >= 0:
                            start_idx = content.find(':', start_idx) + 1
                            content = content[start_idx:].strip()
                            
                    if 'This concludes our analysis. APPROVE' in content:
                        content = content.split('This concludes our analysis. APPROVE')[0].strip()
                        
                    # Generate a timestamped PDF filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"reports/Dashboard_Manual_{timestamp}.pdf"
                    
                    # Save the PDF
                    manual_pdf = save_to_pdf(content, output_path)
                    print(f"Created manual fallback PDF: {manual_pdf}")
            except Exception as e:
                print(f"Manual PDF extraction failed: {e}")
                
    except Exception as e:
        print(f"Error during team chat: {e}")


# Run the async function
if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(run_team_chat())