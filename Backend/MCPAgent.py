#!/usr/bin/env python3
"""
MCPAgent - A Model Context Protocol agent for OpenAI services
Provides communication with OpenAI API via REST endpoints
"""

import autogen
import asyncio
import aiohttp
import json
import os
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCPAgent')

# Enable debug logging for authentication troubleshooting
logging.getLogger('MCPAgent').setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
    exit(1)

# Connection states
class ConnectionState:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class MCPAgent(autogen.AssistantAgent):
    """
    Agent that connects to OpenAI API and integrates with autogen framework
    """
    def __init__(
        self,
        name="MCP_Agent",
        system_message="I am an MCP agent that connects to OpenAI API.",
        mcp_server_url=None,
        max_retries=3,
        retry_delay=2,
        **kwargs
    ):
        # Extract MCP-specific parameters before passing to parent class
        # Create a copy of kwargs to avoid modifying the original
        parent_kwargs = kwargs.copy()
        
        # These parameters shouldn't be passed to the parent class
        if 'max_retries' in parent_kwargs:
            del parent_kwargs['max_retries']
        if 'retry_delay' in parent_kwargs:
            del parent_kwargs['retry_delay']
        if 'mcp_server_url' in parent_kwargs:
            del parent_kwargs['mcp_server_url']
            
        super().__init__(name=name, system_message=system_message, **parent_kwargs)
        
        # Initialize MCP-specific instance variables
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "https://api.openai.com/v1/chat/completions")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.session = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Add connection state tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.last_error = None
        self.connection_attempts = 0
        
        # Set up authentication headers
        self.headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        # Log masked key for debugging
        if self.openai_api_key:
            masked_key = f"****{self.openai_api_key[-4:]}" if len(self.openai_api_key) > 4 else "****"
            logger.debug(f"Using OpenAI API key ending with: {masked_key}")
        
        logger.info(f"Initialized MCP Agent with server URL: {self.mcp_server_url}")

    async def _close_session(self):
        """Helper method to safely close the session"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                logger.debug("Closed existing session")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
        self.session = None

    async def connect_to_mcp(self):
        """
        Establish connection to OpenAI API with authentication
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.connection_state = ConnectionState.CONNECTING
        self.connection_attempts += 1
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Close any existing session
                await self._close_session()
                
                # Create a new session with timeout
                timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
                self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
                
                # Debug log for connection headers
                masked_headers = self.headers.copy()
                if 'Authorization' in masked_headers:
                    masked_headers['Authorization'] = "Bearer ****"
                logger.debug(f"Connection headers: {masked_headers}")
                
                # For OpenAI API, we'll just verify we can access the models endpoint
                test_url = "https://api.openai.com/v1/models"
                async with self.session.get(test_url) as response:
                    status = response.status
                    logger.debug(f"Connection test response: status={status}")
                    
                    if status == 401:
                        response_text = await response.text()
                        self.last_error = f"Authentication failed: Invalid OpenAI API key"
                        logger.error(f"{self.last_error}: {response_text}")
                        self.connection_state = ConnectionState.ERROR
                        return False
                    elif status >= 200 and status < 300:
                        logger.info(f"Successfully connected to OpenAI API")
                        self.connection_state = ConnectionState.CONNECTED
                        return True
                    else:
                        response_text = await response.text()
                        self.last_error = f"Unexpected status code {status}: {response_text}"
                        logger.warning(f"{self.last_error}")
                        
                        if attempt < self.max_retries:
                            wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                            logger.info(f"Retrying connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                            await asyncio.sleep(wait_time)
                        
            except aiohttp.ClientConnectorError as e:
                self.last_error = f"Connection error: {str(e)}"
                logger.error(f"Connection error on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
            except Exception as e:
                self.last_error = f"Failed to create session: {str(e)}"
                logger.error(f"Failed to create session on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to connect to OpenAI API after {self.max_retries} attempts")
        self.connection_state = ConnectionState.ERROR
        return False

    async def send_to_mcp(self, message):
        """
        Send message to OpenAI API with retry logic
        
        Args:
            message: Dictionary containing the message data
            
        Returns:
            dict or None: Response from server or None if error
        """
        # Check connection state and reconnect if needed
        if not self.session or self.connection_state != ConnectionState.CONNECTED:
            connected = await self.connect_to_mcp()
            if not connected:
                logger.error(f"Failed to establish connection to OpenAI API. Last error: {self.last_error}")
                return None
        
        # Use the OpenAI Chat API endpoint
        chat_endpoint = "https://api.openai.com/v1/chat/completions"
        logger.debug(f"Using OpenAI Chat API endpoint: {chat_endpoint}")
        
        # Format the message for OpenAI
        content = message.get("content", "")
        system_prompt = message.get("system", self.system_message)
        model = message.get("model", "gpt-3.5-turbo")
        
        logger.debug(f"Sending message to OpenAI API: {content}")
        
        # Create the OpenAI API request format
        openai_request = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        logger.debug(f"Formatted OpenAI request: {openai_request}")
        
        # Try with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Sending message to OpenAI API (attempt {attempt})")
                
                async with self.session.post(chat_endpoint, json=openai_request) as response:
                    status = response.status
                    logger.debug(f"Response status: {status}")
                    
                    # Read response data
                    try:
                        response_data = await response.text()
                        try:
                            response_json = json.loads(response_data)
                            logger.debug(f"Response data: {response_json}")
                        except json.JSONDecodeError:
                            logger.debug(f"Response is not JSON: {response_data}")
                    except Exception as e:
                        logger.error(f"Error reading response: {e}")
                        response_data = "(Could not read response)"
                    
                    # Handle response based on status code
                    if status == 200:
                        try:
                            result = json.loads(response_data)
                            logger.info("Successfully received response from OpenAI API")
                            
                            # Extract content from OpenAI response format
                            if "choices" in result and len(result["choices"]) > 0:
                                choice = result["choices"][0]
                                content = choice.get("message", {}).get("content", "")
                                return {
                                    "content": content,
                                    "model": result.get("model", ""),
                                    "raw_response": result
                                }
                            
                            # Return the whole response if we can't extract content
                            return result
                        except json.JSONDecodeError:
                            logger.warning(f"Received success status but response is not valid JSON")
                            return {"content": response_data}
                            
                    elif status == 401:
                        self.last_error = "Authentication failed: Invalid OpenAI API key"
                        logger.error(f"{self.last_error}: {response_data}")
                        self.connection_state = ConnectionState.ERROR
                        return None
                    else:
                        self.last_error = f"Error response from OpenAI API: {status} - {response_data}"
                        logger.error(self.last_error)
                        
                        if attempt < self.max_retries:
                            wait_time = self.retry_delay * (2 ** (attempt - 1))
                            logger.info(f"Retrying in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                            await asyncio.sleep(wait_time)
                        else:
                            self.connection_state = ConnectionState.ERROR
                            return None
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.last_error = f"Network error communicating with OpenAI API: {str(e)}"
                logger.error(f"{self.last_error} (attempt {attempt})")
                
                if attempt < self.max_retries:
                    # Check if session is closed and needs to be reopened
                    if self.session and self.session.closed:
                        logger.info("Session was closed, reconnecting...")
                        connected = await self.connect_to_mcp()
                        if not connected:
                            logger.error("Failed to re-establish connection")
                            return None
                    
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    self.connection_state = ConnectionState.ERROR
                    return None
                    
            except Exception as e:
                self.last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error on attempt {attempt}: {str(e)}")
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to send message after {self.max_retries} attempts")
                    self.connection_state = ConnectionState.ERROR
                    return None
                    
        # All attempts failed
        return None

    async def receive_from_mcp(self):
        """
        Receive streaming messages from OpenAI API
        
        This method simulates Server-Sent Events (SSE) handling by making a streaming request to OpenAI.
        
        Returns:
            dict: Parsed response or None if error
        """
        # Check connection state and reconnect if needed
        if not self.session or self.connection_state != ConnectionState.CONNECTED:
            connected = await self.connect_to_mcp()
            if not connected:
                logger.error(f"Failed to establish connection to OpenAI API. Last error: {self.last_error}")
                return None
        
        chat_endpoint = "https://api.openai.com/v1/chat/completions"
        simple_message = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Hello, this is a test message."
                }
            ],
            "stream": True  # Enable streaming for SSE
        }
        
        try:
            logger.debug(f"Starting streaming request to OpenAI API")
            async with self.session.post(chat_endpoint, json=simple_message) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.last_error = f"Error response from OpenAI API: {response.status} - {error_text}"
                    logger.error(self.last_error)
                    return None
                
                logger.debug("Processing stream from OpenAI API")
                # Process streamed response
                buffer = ""
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        logger.debug(f"Stream line: {decoded_line}")
                        
                        # Stream format: "data: {JSON}"
                        if decoded_line.startswith("data:"):
                            if decoded_line == "data: [DONE]":
                                logger.debug("Stream completed")
                                break
                                
                            data_json = decoded_line[5:].strip()
                            try:
                                parsed_data = json.loads(data_json)
                                # Return the first chunk as a sample
                                if parsed_data.get("choices") and len(parsed_data["choices"]) > 0:
                                    choice = parsed_data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                        logger.debug(f"Received content: {content}")
                                        return {
                                            "content": content,
                                            "type": "chunk",
                                            "model": parsed_data.get("model", ""),
                                            "raw": parsed_data
                                        }
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse streaming data: {e}")
                    
                # If we got here without returning anything, construct a default response
                return {
                    "content": "Test response from OpenAI API",
                    "type": "test",
                    "model": "gpt-3.5-turbo"
                }
                    
        except Exception as e:
            self.last_error = f"Error in stream handling: {str(e)}"
            logger.error(self.last_error)
            return None

    async def close_connection(self):
        """
        Close the session and clean up resources
        
        Ensures proper cleanup of any open connections
        """
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                logger.info("Closed OpenAI API connection")
            self.session = None
            self.connection_state = ConnectionState.DISCONNECTED
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
        finally:
            # Ensure the session is nullified even if closing fails
            self.session = None
            self.connection_state = ConnectionState.DISCONNECTED

    def generate_reply(self, messages=None, sender=None, config=None):
        """
        Override the generate_reply method to integrate with OpenAI API
        
        Args:
            messages: The messages in the conversation
            sender: The sender of the message
            config: Optional configuration for the agent (default: None)
            
        Returns:
            str: Response from the OpenAI API or error message
        """
        # If no messages provided, return empty response
        if not messages:
            return ""
        
        async def process_with_mcp():
            """Async function to process messages with OpenAI API"""
            try:
                # Connect to OpenAI API if not connected
                if not self.session or self.connection_state != ConnectionState.CONNECTED:
                    connected = await self.connect_to_mcp()
                    if not connected:
                        logger.error(f"Failed to connect to OpenAI API: {self.last_error}")
                        return f"Error: Failed to connect to OpenAI API. {self.last_error}"

                # Process the last message
                last_message = messages[-1]["content"]
                
                # Send to OpenAI API and get response
                api_response = await self.send_to_mcp({
                    "model": "gpt-3.5-turbo",
                    "system": self.system_message,
                    "content": last_message,
                    "sender": sender.name if sender else "unknown"
                })

                if api_response:
                    return api_response.get("content", "No response from OpenAI API")
                return f"Failed to get response from OpenAI API. Last error: {self.last_error}"
            finally:
                # We don't close the connection here to allow for reuse
                # It will be closed when the agent is destroyed or explicitly closed
                pass

        # Run the async function in the event loop
        try:
            # Check if we already have a running event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to use create_task
                future = asyncio.run_coroutine_threadsafe(process_with_mcp(), loop)
                response = future.result(timeout=60)  # 60 second timeout
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(process_with_mcp())
        except Exception as e:
            logger.error(f"Error processing OpenAI API request: {str(e)}")
            response = f"An error occurred while processing your request: {str(e)}"
        
        return response

# Example usage
if __name__ == "__main__":
    # Define the configuration dictionary
    config = {
        "llm_config": {
            "config_list": [
                {
                    "model": "gpt-3.5-turbo",
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            ]
        },
        "code_execution_config": {
            "use_docker": False  # Run without Docker
        }
    }
    
    # Create an MCP agent
    mcp_agent = MCPAgent(
        name="MCP_Agent",
        llm_config=config["llm_config"],
        code_execution_config=config["code_execution_config"]
    )
    
    # Create a user proxy
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=1,
        llm_config=None,  # User proxy doesn't need LLM config
        code_execution_config={"use_docker": False}  # Disable Docker for code execution
    )
    
    # Start a conversation
    user_proxy.initiate_chat(
        mcp_agent,
        message="Hello, can you help me with a task?"
    )
