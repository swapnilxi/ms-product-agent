from MCPAgent import MCPAgent
import autogen

def main():
    # Configure the MCP agent
    mcp_agent = MCPAgent(
        name="MCP_Agent",
        system_message="I am an MCP agent that helps with tasks and connects to the Neon MCP server."
    )

    # Create a user proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=1
    )

    # Start the conversation
    user_proxy.initiate_chat(
        mcp_agent,
    message="Hello, can you help me analyze some data in AI RAG Chatbot database on neon?"
    )

if __name__ == "__main__":
    main() 