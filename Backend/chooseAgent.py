# chooseAgent.py

from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
import researchAgent
import productAgent
import marketingAgent
from agent_pipeline import run_agent_team

async def run_chosen_agents(selected_agents: list):
    valid_agents = {"research", "product", "marketing", "pipeline"}
    selected_agents = [agent.lower() for agent in selected_agents if agent.lower() in valid_agents]

    if not selected_agents:
        return {"status": "error", "message": "No valid agents selected."}

    cancellation_token = CancellationToken()
    results = {}
    previous_message = None

    if "pipeline" in selected_agents:
        selected_agents = ["research", "product", "marketing"]

    for agent in selected_agents:
        if agent == "research":
            if "research_output" not in results:
                print("Running Research Agent...")
                research_result = await run_agent_team(
                    team=researchAgent.group_chat,
                    task="Start by discussing Microsoft and Samsung current operations and XR future.",
                    cancellation_token=cancellation_token,
                )
                previous_message = research_result.messages[-1]
                results['research_output'] = previous_message.content

        elif agent == "product":
            if "research_output" not in results:
                print("Auto-running Research Agent for Product Agent...")
                research_result = await run_agent_team(
                    team=researchAgent.group_chat,
                    task="Start by discussing Microsoft and Samsung current operations and XR future.",
                    cancellation_token=cancellation_token,
                )
                previous_message = research_result.messages[-1]
                results['research_output'] = previous_message.content

            print("Running Product Agent...")
            product_result = await run_agent_team(
                team=productAgent.team,
                task=[TextMessage(content=results['research_output'], source="research_agent")],
                cancellation_token=cancellation_token,
            )
            previous_message = product_result.messages[-1]
            results['product_output'] = previous_message.content

        elif agent == "marketing":
            marketing_input = results.get('product_output') or results.get('research_output')

            if not marketing_input:
                print("Auto-running Research Agent for Marketing Agent...")
                research_result = await run_agent_team(
                    team=researchAgent.group_chat,
                    task="Start by discussing Microsoft and Samsung current operations and XR future.",
                    cancellation_token=cancellation_token,
                )
                previous_message = research_result.messages[-1]
                results['research_output'] = previous_message.content
                marketing_input = results['research_output']

            print("Running Marketing Agent...")
            marketing_result = await run_agent_team(
                team=marketingAgent.team,
                task=[TextMessage(content=marketing_input, source="input_agent")],
                cancellation_token=cancellation_token,
            )
            previous_message = marketing_result.messages[-1]
            results['marketing_output'] = previous_message.content

    return {"status": "success", "agents_run": selected_agents, "results": results}
