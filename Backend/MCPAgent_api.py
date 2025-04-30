
import os
from fastapi import APIRouter, Query
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent

load_dotenv()

router = APIRouter()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://mcp.neon.tech/sse")

# This is the assistant agent (can be used in conversations)
assistant_agent = AssistantAgent(
    name="MCP_Assistant",
    system_message="You are a helpful assistant connected to Neon MCP services."
)

# Simplified MCPAgent using AssistantAgent as base
class MCPAgent(AssistantAgent):
    def __init__(self, name="MCPAgent", **kwargs):
        super().__init__(name=name, system_message="MCP connection agent", **kwargs)
        self.mcp_url = MCP_SERVER_URL
        self.api_key = OPENAI_API_KEY

    async def query(self, prompt: str):
        # Replace with actual MCP/OpenAI logic if needed
        prompt= "tell me about neon databases"
        return f"[MCPAgent] Simulated response to: '{prompt}'"

# Create a single instance to reuse
mcp_agent = MCPAgent()

@router.get("/mcp-agent")
async def run_mcp_agent(prompt: str = Query("Tell me about Neon databases", description="Your query to MCP agent")):
    response = await mcp_agent.query(prompt)
    return {"response": response}
