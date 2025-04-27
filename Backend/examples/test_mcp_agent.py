#!/usr/bin/env python3
"""
Interactive Database Assistant - Query Neon databases with MCPAgent and OpenAI.

This script:
1. Creates an interactive CLI for database querying
2. Uses MCPAgent to communicate with OpenAI GPT-4o-mini model
3. Includes the Neon API key context for database insights
4. Provides a user-friendly interface with clean formatting
"""

import os
import asyncio
import logging
import sys
import json
import subprocess
from dotenv import load_dotenv
from MCPAgent import MCPAgent

# Configure logging - set to WARNING to reduce verbosity
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('DB_Query_Test')

# Set other loggers to WARNING level too
logging.getLogger('MCPAgent').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY environment variable is not set.")
    sys.exit(1)

if not os.getenv("neon_api_key"):
    logger.error("neon_api_key environment variable is not set.")
    sys.exit(1)

def get_neon_api_response(endpoint):
    """Get direct response from Neon API for context"""
    try:
        neon_api_key = os.getenv("neon_api_key")
        cmd = [
            "curl", "-s",
            "-H", f"Authorization: Bearer {neon_api_key}",
            f"https://console.neon.tech/api/v2/{endpoint}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        logger.error(f"Error querying Neon API: {e}")
        return f"Error: {str(e)}"

async def interactive_database_query():
    """Interactive console for database querying using MCPAgent"""
    mcp_agent = None
    
    try:
        print("\n🔍 \033[1;36mNeon Database Assistant\033[0m 🔍")
        print("Initializing connection to OpenAI and gathering context...")
        
        # Get Neon API context
        neon_api_key = os.getenv("neon_api_key")
        masked_key = f"****{neon_api_key[-4:]}" if len(neon_api_key) > 4 else "****"
        
        # Try to get projects info for context
        projects_info = get_neon_api_response("projects")
        
        # Create system prompt with context
        system_prompt = f"""
You are a database expert assistant specialized in working with Neon Postgres databases.
You help users understand their database setup and provide information about their databases.

Context about the user's Neon setup:
- The user has a Neon API key ending with: {masked_key}
- Neon API projects endpoint response: {projects_info}

Keep your responses concise and focused on the user's questions about their databases.
Format information in an easy-to-read way with bullet points and section headers where appropriate.
If the Neon API is not accessible, suggest alternative ways to check database information.
"""
        # Create the MCPAgent with database-focused system message
        mcp_agent = MCPAgent(
            name="DB_Query_Agent",
            system_message=system_prompt,
            max_retries=2
        )
        
        # Connect to OpenAI API
        connected = await mcp_agent.connect_to_mcp()
        if not connected:
            print(f"❌ Error: Failed to connect to OpenAI API")
            return
        
        print("✅ Connected to AI service! Ask anything about your Neon databases.")
        print("Type 'exit' or 'quit' to end the session.\n")
        
        # Initial query to show database overview
        initial_query = "Give me a quick overview of my Neon databases."
        print(f"\033[1;34m> Automatically querying: {initial_query}\033[0m")
        
        # Send query to MCPAgent
        response = await mcp_agent.send_to_mcp({
            "model": "gpt-4o-mini",  # Use GPT-4o-mini as requested
            "system": system_prompt,
            "content": initial_query
        })
        
        # Handle and display the response
        if response:
            content = response.get("content", "")
            print("\n\033[1;32m" + "─" * 80 + "\033[0m")  # Green separator
            print(content)
            print("\033[1;32m" + "─" * 80 + "\033[0m\n")  # Green separator
        else:
            print("❌ Failed to get response from AI service")
            return
        
        # Interactive loop for user questions
        while True:
            try:
                user_query = input("\033[1;33mAsk about your databases (or type 'exit' to quit): \033[0m")
                
                # Check for exit command
                if user_query.lower() in ['exit', 'quit', 'q', 'bye']:
                    print("Goodbye! Closing database assistant...")
                    break
                
                # Skip empty questions
                if not user_query.strip():
                    continue
                
                print("Processing your question...")
                
                # Send query to MCPAgent
                response = await mcp_agent.send_to_mcp({
                    "model": "gpt-4o-mini",  # Use GPT-4o-mini as requested
                    "system": system_prompt,
                    "content": user_query
                })
                
                # Handle and display the response
                if response:
                    content = response.get("content", "")
                    print("\n\033[1;32m" + "─" * 80 + "\033[0m")  # Green separator
                    print(content)
                    print("\033[1;32m" + "─" * 80 + "\033[0m\n")  # Green separator
                else:
                    print("❌ Failed to get response")
            
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"❌ Error processing your question: {str(e)}")
        
        # Clean up
        if mcp_agent:
            await mcp_agent.close_connection()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if mcp_agent:
            await mcp_agent.close_connection()

def main():
    """Main function to run the interactive database assistant"""
    try:
        asyncio.run(interactive_database_query())
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    print("Database assistant closed.")

if __name__ == "__main__":
    main()
