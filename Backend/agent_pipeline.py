#https://chatgpt.com/share/680e8d2b-a27c-800c-bc2a-70a527424c5f
# agent_pipeline.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from save_report import save_pipeline_report

# Import the agents
import researchAgent 
import marketingAgent 
import productAgent


# agent runner 
async def run_agent_team(team, task, cancellation_token: CancellationToken):
    
    await team.reset()

    chat_result = await team.run(
        task=task,
        cancellation_token=cancellation_token,
    )

    # 🖨️ Print conversation
    for message in chat_result.messages:
        print(f"[{message.source}] {message.content}\n")

    return chat_result

async def run_full_pipeline(company1=None, company2=None, user_input=None):
    
    cancellation_token = CancellationToken()

    results = {}
    previous_message = None
    # Generate initial task
    if company1 and company2 and user_input:
        initial_task = (
            f"Think and make a collaborative product between {company1} and {company2}."
            f"\n\nUser Instruction: {user_input.strip()}"
        )
    else:
        # Default task
        initial_task = "Think and make a collaborative product between Microsoft and Samsung in XR field."

    # Step 1: Run Research Agent
    # Research Agent
    research_result = await researchAgent.run_agent(
        task=[TextMessage(content=initial_task, source="user")],
        cancellation_token=cancellation_token
    )
    research_message = research_result.messages[-1]
    results['research_output'] = research_message.content
    
    # Product Agent
    product_result = await productAgent.run_agent(
        task=[TextMessage(content=research_message.content, source=research_message.source)],
        cancellation_token=cancellation_token
    )
    product_message = product_result.messages[-1]
    results['product_output'] = product_message.content

    # Marketing Agent
    marketing_result = await marketingAgent.run_agent(
        task=[TextMessage(content=product_message.content, source=product_message.source)],
        cancellation_token=cancellation_token
    )
    marketing_message = marketing_result.messages[-1]
    results['marketing_output'] = marketing_message.content
    
    # Save report
    report_path = save_pipeline_report(results)
    print(f"✅ Report saved at: {report_path}")

    return results

if __name__ == "__main__":
    results = asyncio.run(research_to_marketing_flow())
    print("Research Output:", results['research_output'])