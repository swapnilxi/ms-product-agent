import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

from utils.pdf_generator import capture_and_save_dashboard_output, save_to_pdf

# Load environment variables
load_dotenv()

class AgentFactory:
    """Factory class for creating agents with consistent formatting and behavior."""
    
    def __init__(self, model_client: OpenAIChatCompletionClient):
        self.model_client = model_client
        self.format_instruction = """
        IMPORTANT FORMAT INSTRUCTION:
        1. Your response MUST be clear, concise, and focused only on your specific role.
        2. NEVER perform another agent's job - stay strictly within your assigned role.
        3. ALWAYS end your message by explicitly passing the conversation to the next agent by name.
        4. Format your message with clear headings and bullet points for easy readability.
        """
    
    def create_agent(self, name: str, system_message_template: str, next_agent: str = None, 
                    tools: List = None) -> AssistantAgent:
        """
        Create an agent with standardized formatting and next-agent handling.
        
        Args:
            name: Name of the agent
            system_message_template: System message (will have format instructions added)
            next_agent: Name of the next agent in workflow (optional)
            tools: List of tools for the agent (optional)
        
        Returns:
            Configured AssistantAgent
        """
        # Add format instructions
        system_message = f"{system_message_template}\n\n{self.format_instruction}"
        
        # Add next agent handoff if provided
        if next_agent:
            system_message += f"\n\nAfter your analysis, end with the phrase: \"I now pass the conversation to the {next_agent}.\""
            
        return AssistantAgent(
            name=name,
            system_message=system_message,
            model_client=self.model_client,
            tools=tools or []
        )


class CollaborationTeam:
    """Manages a team of agents for collaborative analysis and planning."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the collaboration team.
        
        Args:
            model_config: Configuration for the model client
        """
        # Create model client
        self.model_client = OpenAIChatCompletionClient(**model_config)
        
        # Create agent factory
        self.agent_factory = AgentFactory(self.model_client)
        
        # Create agents
        self.agents = self._create_agents()
        
        # Define termination condition
        self.termination_condition = TextMentionTermination("This concludes our analysis. APPROVE")
        
        # Create team
        self.team = SelectorGroupChat(
            self.agents,
            termination_condition=self.termination_condition,
            model_client=self.model_client
        )
    
    def _create_agents(self) -> List[AssistantAgent]:
        """Create all agents for the collaboration team."""
        
        agents = []
        
        # Microsoft Expert
        agents.append(self.agent_factory.create_agent(
            name="MicrosoftExpert",
            system_message_template="""You are an expert EXCLUSIVELY on Microsoft's products, services, market position, and business strategies.
            
            Your ONLY job is to provide a detailed analysis of Microsoft's latest products or initiatives.
            
            CRITICAL: You must ONLY discuss Microsoft products and services. DO NOT mention Samsung or any Samsung products.
            DO NOT propose any collaboration ideas - that is another agent's job.""",
            next_agent="Samsung expert"
        ))
        
        # Samsung Expert
        agents.append(self.agent_factory.create_agent(
            name="SamsungExpert",
            system_message_template="""You are an expert EXCLUSIVELY on Samsung's products, services, market position, and business strategies.
            
            Your ONLY job is to provide a detailed analysis of Samsung's latest products or initiatives.
            
            CRITICAL: You must ONLY discuss Samsung products and services. DO NOT mention Microsoft products or propose any collaboration ideas.""",
            next_agent="Innovation agent"
        ))
        
        # Innovation Agent
        agents.append(self.agent_factory.create_agent(
            name="InnovationAgent",
            system_message_template="""You identify innovative collaborative projects between Microsoft and Samsung, focusing on unique selling points and requirements.
            
            Based on the information from both company experts, propose 2-3 innovative collaboration ideas.
            
            IMPORTANT: Check if the Review agent has previously DISAPPROVED an idea. If so, propose completely new ideas.
            
            Format your ideas with clear headings and bullet points.""",
            next_agent="Marketing Research agent"
        ))
        
        # Marketing Research Agent
        agents.append(self.agent_factory.create_agent(
            name="MarketingResearchAgent",
            system_message_template="""You analyze sales data country-wise and identify market trends for Microsoft-Samsung collaborations.
            
            Based on the innovative ideas proposed, identify the top markets globally that would be receptive to these collaborations.
            
            Only respond if the Innovation agent has successfully proposed ideas.
            
            Format your market analysis with clear headings, tables, and bullet points.""",
            next_agent="Marketing Plan agent"
        ))
        
        # Marketing Plan Agent
        agents.append(self.agent_factory.create_agent(
            name="MarketingPlanAgent",
            system_message_template="""You develop detailed marketing plans for the top 3 performing countries.
            
            Based on the market research, create a concise marketing strategy for the top markets identified.
            
            Only respond if the Marketing Research agent has successfully identified markets.
            
            Format your marketing plan with clear headings, bullet points, and timelines.""",
            next_agent="Review agent"
        ))
        
        # Review Agent
        agents.append(self.agent_factory.create_agent(
            name="ReviewAgent",
            system_message_template="""You review and summarize the outputs from other agents, creating concise reports.
            
            Create an executive summary of all the insights and plans shared by previous agents.
            
            After your summary, you must decide to either:
            1. ACCEPT the plan: End your message with "This plan is ACCEPTED. I now pass the conversation to the Dashboard agent."
            2. REJECT the plan: End your message with "This plan is REJECTED. I now pass the conversation back to the Innovation agent."

            IMPORTANT: When rejecting, NEVER use the word "APPROVE" anywhere in your message.
            
            If you REJECT, explicitly ask the Innovation agent to propose new ideas and all other agents should wait until new ideas are proposed.
            If you ACCEPT, the Dashboard agent should proceed with creating the dashboard."""
        ))
        
        # Dashboard Agent
        agents.append(self.agent_factory.create_agent(
            name="DashboardAgent",
            system_message_template="""You prepare dashboard data for higher management and handle customer support inquiries.

            IMPORTANT: Only respond if the Review agent has ACCEPTED the plan. If the review is not yet accepted, simply state "Waiting for plan acceptance" and pass back to the Review agent.

            Based on all the information shared, provide key metrics and dashboard elements that would be useful for tracking the success of these initiatives.
            
            Format your dashboard recommendations in clear sections with:
            - Key Performance Indicators (KPIs)
            - Visualization recommendations
            - Data sources
            - Update frequency
            
            You are the final agent in this conversation. After providing your dashboard recommendations, end your message with the exact phrase: "This concludes our analysis. APPROVE"

            If you see that a previous cycle was REJECTED, wait for a new accepted plan before creating your dashboard."""
        ))
        
        return agents
    
    async def reset(self):
        """Reset the team for a new task."""
        await self.team.reset()
    
    async def run_team_chat(self, task: str, delay_between_messages: float = 10):
        """
        Run the team chat with the given task.
        
        Args:
            task: The task to run
            delay_between_messages: Delay between agent messages in seconds
            
        Returns:
            Path to the generated PDF if successful, None otherwise
        """
        # Create cancellation token
        cancellation_token = CancellationToken()
        
        # Reset team for new task
        await self.reset()
        
        # Store all messages and specifically track the final message
        all_messages = []
        final_message = None
        
        # Run team chat
        try:
            async for message in self.team.run_stream(
                    task=task, 
                    cancellation_token=cancellation_token
            ):
                print(message)
                all_messages.append(message)
                final_message = message  # Keep track of the final message
                
                # Optional: Add a small delay between agent responses for readability
                await asyncio.sleep(delay_between_messages)
            
            # Process output and generate PDF
            return self._process_output(all_messages, final_message)
            
        except Exception as e:
            print(f"Error during team chat: {e}")
            return None
    
    def _process_output(self, all_messages, final_message):
        """Process chat output and generate PDF."""
        # Try primary PDF creation method
        pdf_path = capture_and_save_dashboard_output(all_messages)
        
        # If normal extraction fails, try with just the final message
        if not pdf_path and final_message:
            pdf_path = capture_and_save_dashboard_output([final_message])
            
        if pdf_path:
            print(f"\nDashboard successfully saved to PDF: {pdf_path}")
            return pdf_path
        
        # Create a manual extraction as a last resort
        return self._create_fallback_pdf(final_message)
    
    def _create_fallback_pdf(self, final_message):
        """Create a fallback PDF when normal methods fail."""
        try:
            if final_message:
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
                return manual_pdf
        except Exception as e:
            print(f"Manual PDF extraction failed: {e}")
        
        return None


def create_default_task():
    """Create the default task for the collaboration team."""
    return """
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


async def main():
    """Main function to run the collaboration team."""
    # Configure model client
    model_config = {
        "model": "gemini-1.5-flash-8b",
        "api_key": os.environ.get("API_KEY"),
        "temperature": 0.2,
        "max_tokens": 1500,
    }
    
    # Create collaboration team
    team = CollaborationTeam(model_config)
    
    # Create task
    task = create_default_task()
    
    # Run team chat
    pdf_path = await team.run_team_chat(task)
    
    # Report results
    if pdf_path:
        print(f"Collaboration analysis completed successfully. PDF saved to: {pdf_path}")
    else:
        print("Collaboration analysis completed, but no PDF was generated.")


if __name__ == "__main__":
    asyncio.run(main())