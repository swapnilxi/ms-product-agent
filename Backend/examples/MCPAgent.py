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

# Check for Neon API key
if not os.getenv("NEON_API_KEY"):
    logger.warning("NEON_API_KEY environment variable is not set. MCP server functionality may not work.")
    logger.warning("Please set NEON_API_KEY in your .env file if you plan to use Neon MCP server.")

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
        neon_api_key=None,
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
        if 'neon_api_key' in parent_kwargs:
            del parent_kwargs['neon_api_key']
            
        # Initialize parent class
        super().__init__(name=name, system_message=system_message, **parent_kwargs)
            
        # Initialize MCP-specific instance variables
        # Initialize MCP-specific instance variables
        # Initialize MCP-specific instance variables
        raw_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "https://mcp.neon.tech/sse")
        # Validate and normalize the server URL
        if not raw_server_url or not isinstance(raw_server_url, str):
            logger.error("Invalid MCP server URL - using default")
            raw_server_url = "https://mcp.neon.tech/api"
            
        # Ensure URL has correct format and doesn't have trailing slashes
        if not raw_server_url.startswith(("http://", "https://")):
            logger.warning(f"Adding https:// prefix to MCP server URL: {raw_server_url}")
            raw_server_url = f"https://{raw_server_url}"
            
        # Ensure URL doesn't have trailing slashes for consistent path joining
        self.mcp_server_url = raw_server_url.rstrip('/')
        logger.debug(f"Normalized MCP server URL: {self.mcp_server_url}")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Get and validate Neon API key
        raw_neon_key = neon_api_key or os.getenv("NEON_API_KEY", "")
        
        # Normalize the key by removing whitespace and any Bearer prefix
        self.neon_api_key = raw_neon_key.strip()
        if self.neon_api_key.lower().startswith("bearer "):
            self.neon_api_key = self.neon_api_key[7:].strip()
            logger.debug("Removed 'Bearer' prefix from Neon API key")
            
        # Validate Neon API key format - should typically start with "neon_"
        if self.neon_api_key:
            if not self.neon_api_key.startswith("neon_"):
                logger.warning("Neon API key does not start with 'neon_' prefix - this may not be a valid Neon key")
                logger.warning("Authentic Neon API keys typically start with 'neon_' prefix")
            elif len(self.neon_api_key) < 10:
                logger.warning("Neon API key appears too short to be valid")
        else:
            logger.warning("No Neon API key provided - MCP server authentication will fail")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Add connection state tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.last_error = None
        self.connection_attempts = 0
        self.event_loop = None
        
        # Set up authentication headers for MCP server using Neon API key
        # Check if the key is available and format it correctly
        if not self.neon_api_key:
            logger.warning("No Neon API key available - MCP server authentication will fail")
            
        # Construct headers with proper format
        # Construct headers with proper format
        self.mcp_headers = {
            "Authorization": f"Bearer {self.neon_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        # Validate header format
        auth_header = self.mcp_headers.get("Authorization", "")
        if not auth_header or auth_header == "Bearer " or auth_header == "Bearer":
            logger.error("Invalid Authorization header format - authentication will fail")
        
        # Headers for OpenAI API
        self.openai_headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        # This is a duplicate, remove it
        
        # Set up authentication headers - use mcp_headers instead of duplicate headers
        # This is kept for backward compatibility with existing code
        # Log masked keys for debugging
        if self.openai_api_key:
            masked_key = f"****{self.openai_api_key[-4:]}" if len(self.openai_api_key) > 4 else "****"
            logger.debug(f"Using OpenAI API key ending with: {masked_key}")
        
        if self.neon_api_key:
            if len(self.neon_api_key) > 8:
                # Show more key details for better debugging
                first_four = self.neon_api_key[:4]
                last_four = self.neon_api_key[-4:]
                masked_key = f"{first_four}...{last_four}"
                logger.debug(f"Using Neon API key pattern: {masked_key}")
                logger.debug(f"Neon API key length: {len(self.neon_api_key)} characters")
                
                # Add detailed validation info for debugging
                if first_four == "neon":
                    logger.debug("Neon API key has the correct 'neon' prefix")
                else:
                    logger.warning(f"Neon API key has unexpected prefix: '{first_four}'")
                    logger.warning("Authentic Neon API keys should start with 'neon_'")
            else:
                logger.warning("Neon API key is too short - authentication may fail")
        else:
            logger.warning("No NEON_API_KEY provided - MCP server access will not work")
        
        logger.info(f"Initialized MCP Agent with server URL: {self.mcp_server_url}")
        # Initialize session to None - will be created when needed
        self.session = None
        self.connection_state = ConnectionState.DISCONNECTED
        # Define OpenAI API URL
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        logger.debug("MCPAgent initialized - session will be created when needed")

    async def _close_session(self):
        """Helper method to safely close the session"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                logger.debug("Closed existing session")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
        self.session = None
        
    async def _create_session(self):
        """Helper method to safely create a new session"""
        if self.session is None or self.session.closed:
            try:
                self.session = aiohttp.ClientSession()
                self.connection_state = ConnectionState.CONNECTING
                logger.debug("Created new aiohttp session")
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                self.session = None
                self.connection_state = ConnectionState.ERROR
                raise

    async def connect_to_mcp(self):
        """
        Connect to the MCP server and test the connection
        
        Returns:
            bool: True if successfully connected, False otherwise
        """
        logger.info(f"Connecting to MCP server at {self.mcp_server_url}")
        self.connection_state = ConnectionState.CONNECTING
        self.connection_attempts += 1
        
        # Create a new session if needed
        if not self.session or self.session.closed:
            await self._create_session()
        
        # Try to connect with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Testing MCP connection (attempt {attempt}/{self.max_retries})")
                # Try multiple endpoint paths for better compatibility
                test_endpoints = ["/v1/status", "/v1/health", "/status", "/health", "/v1/ping", "/ping", ""]
                
                for endpoint in test_endpoints:
                    try:
                        test_url = f"{self.mcp_server_url}{endpoint}"
                        logger.debug(f"Testing connection to: {test_url}")
                        
                        # Set a specific timeout for connection attempts
                        timeout = aiohttp.ClientTimeout(total=10, connect=5)
                        async with self.session.get(
                            test_url, 
                            headers=self.mcp_headers,
                            timeout=timeout
                        ) as response:
                            status = response.status
                            logger.debug(f"MCP server response: endpoint={endpoint}, status={status}")
                            
                            # Check if we got a successful response
                            if status == 200:
                                response_text = await response.text()
                                logger.debug(f"Server response: {response_text[:100]}...")
                                self.connection_state = ConnectionState.CONNECTED
                                logger.info(f"Successfully connected to MCP server using endpoint: {endpoint}")
                                return True
                            
                            # If we got a 404 on this endpoint, try the next one
                            if status == 404:
                                if endpoint:
                                    logger.debug(f"Endpoint {endpoint} not found, trying next endpoint")
                                else:
                                    logger.debug(f"Base URL {test_url} returned 404, trying next endpoint")
                                
                                # After trying all endpoints, provide more debugging info
                                if endpoint == test_endpoints[-1]:
                                    logger.warning(f"All endpoints returned 404. Please verify the base URL: {self.mcp_server_url}")
                                    logger.warning("Common Neon MCP base URLs: https://mcp.neon.tech/api, https://api.neon.tech")
                                
                                continue
                            
                            # For other status codes, handle response
                            response_text = await response.text()
                            
                            # Special handling for authentication errors
                            if status == 401:
                                self.last_error = "Authentication failed: Invalid Neon API key"
                                logger.error(f"{self.last_error}. Response: {response_text}")
                                logger.error("Please check your NEON_API_KEY environment variable")
                                self.connection_state = ConnectionState.ERROR
                                
                                # Skip to authentication error handling
                                # Skip to authentication error handling
                                break
                    except aiohttp.ClientConnectorError as e:
                        self.last_error = f"Connection error to MCP server: {str(e)}"
                        logger.error(self.last_error)
                        # Connection error is terminal, don't try other endpoints
                        break
                    except Exception as e:
                        self.last_error = f"Error testing endpoint {endpoint}: {str(e)}"
                        logger.error(self.last_error)
                        # Try next endpoint
                        continue
                
                # If we've tried all endpoints and none worked, consider connection failed
                logger.error("All connection endpoints failed. Please check server URL and credentials.")
                self.connection_state = ConnectionState.ERROR
                
                # Handle authentication errors (401) outside the endpoint loop
                if 'status' in locals() and status == 401:
                    logger.error("Authentication error. Please check your NEON_API_KEY environment variable")
                    
                    # Check for common authentication errors with Neon API key
                    if not self.neon_api_key.startswith("neon_"):
                        logger.error("ERROR: Your Neon API key does not start with 'neon_' prefix") 
                        logger.error("Neon API keys should start with 'neon_' - please check your key format")
                        # Log the first few characters of the key for debugging (safely)
                        if self.neon_api_key:
                            prefix = self.neon_api_key[:4] if len(self.neon_api_key) > 8 else ""
                            suffix = self.neon_api_key[-4:] if len(self.neon_api_key) > 8 else ""
                            if prefix and suffix:
                                logger.debug(f"Key format check: starts with '{prefix}...{suffix}'")
                            logger.debug(f"Key length: {len(self.neon_api_key)} characters")
                        else:
                            logger.error("Neon API key is empty")
                            
                        # Show the exact header being sent (with key redacted)
                        auth_header = self.mcp_headers.get("Authorization", "")
                        if auth_header:
                            parts = auth_header.split(" ", 1)
                            if len(parts) > 1:
                                prefix = parts[0]
                                value = parts[1]
                                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                                logger.debug(f"Auth header format: '{prefix} {masked_value}'")
                            else:
                                logger.error("Malformed Authorization header")
                        
                        # If we're on the last attempt, provide more guidance
                        if attempt == self.max_retries:
                            logger.error("Authentication guidance:")
                            logger.error("1. Check if your NEON_API_KEY is correctly set in .env file")
                            logger.error("2. Make sure it doesn't have extra quotes or spaces")
                            logger.error("3. Ensure it's the correct key for the Neon MCP service")
                            logger.error("4. The key should NOT include 'Bearer' - that's added automatically")
                            logger.error("5. Neon API keys should start with 'neon_' prefix")
                            logger.error(f"   Your key starts with: '{self.neon_api_key[:5]}...'")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying MCP connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                
            except aiohttp.ClientConnectorError as e:
                self.last_error = f"MCP server connection error: {str(e)}"
                logger.error(f"Connection error on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying MCP connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
            except Exception as e:
                self.last_error = f"Unexpected error connecting to MCP server: {str(e)}"
                logger.error(f"Unexpected error on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying MCP connection in {wait_time} seconds (attempt {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to connect to MCP server after {self.max_retries} attempts")
        self.connection_state = ConnectionState.ERROR
        return False
    async def process_with_openai(self, message: str) -> str:
        """
        Process a message with the OpenAI API
        
        Args:
            message: The user's message to process
            
        Returns:
            The response from the API
        """
        # Define the URL
        openai_endpoint = self.openai_api_url
        logger.debug(f"Using OpenAI Chat API endpoint: {openai_endpoint}")
        logger.debug(f"Sending message to OpenAI API: {message}")
        
        # Structure the API request
        request_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": message}
            ]
        }
        
        logger.debug(f"Formatted OpenAI request: {request_data}")
        
        # Make the request with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Sending message to OpenAI API (attempt {attempt})")
                
                if not self.session or self.session.closed:
                    await self._create_session()
                
                async with self.session.post(
                    openai_endpoint,
                    headers=self.openai_headers,
                    json=request_data,
                    timeout=30
                ) as response:
                    status = response.status
                    logger.debug(f"Response status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        logger.debug(f"Response data: {data}")
                        
                        # Extract the assistant's message from the response
                        if 'choices' in data and len(data['choices']) > 0:
                            logger.info("Successfully received response from OpenAI API")
                            return data['choices'][0]['message']['content']
                        else:
                            raise ValueError("No valid choices in API response")
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
        # Check connection state and reconnect if needed
        if not self.session or self.connection_state != ConnectionState.CONNECTED:
            connected = await self.connect_to_mcp()
            if not connected:
                logger.error(f"Failed to establish connection to MCP server. Last error: {self.last_error}")
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

    async def query_mcp(self, user_query: str) -> dict:
        """
        Query the MCP server with a user question
        
        Args:
            user_query: User's question to process
            
        Returns:
            dict: Parsed response or None if error
        """
        # Check connection state and reconnect if needed
        if not self.session or self.connection_state != ConnectionState.CONNECTED:
            connected = await self.connect_to_mcp()
            if not connected:
                logger.error(f"Failed to establish connection to MCP server. Last error: {self.last_error}")
                return None
        
        # Prepare the query payload for MCP server
        # Prepare the query payload for MCP server
        query_payload = {
            "query": user_query,
            "stream": True  # Enable streaming for SSE
        }
        logger.debug(f"Sending query to MCP server: {user_query}")
        
        # Use the base URL as is since it now includes /sse
        query_url = self.mcp_server_url
        # Set a timeout context for better error handling
        # Set a timeout context for better error handling
        timeout = aiohttp.ClientTimeout(total=60)
        try:
            # Make a POST request to the MCP server with the query
            async with self.session.post(
                query_url,
                headers=self.mcp_headers,
                json=query_payload,
                timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.last_error = f"Error response from MCP server: {response.status} - {error_text}"
                    logger.error(self.last_error)
                    return None
                
                logger.debug("Processing SSE stream from MCP server")
                
                # Process the SSE stream
                full_response = ""
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        logger.debug(f"SSE line: {decoded_line}")
                        
                        # SSE format: "data: {JSON}"
                        if decoded_line.startswith("data:"):
                            if decoded_line == "data: [DONE]":
                                logger.debug("SSE stream completed")
                                break
                            
                            data_json = decoded_line[5:].strip()
                            try:
                                parsed_data = json.loads(data_json)
                                # Extract content if available
                                if "content" in parsed_data:
                                    content = parsed_data["content"]
                                    full_response += content
                                    logger.debug(f"Received content chunk: {content}")
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse SSE data: {e}")
                
                # Return the complete response
                if full_response:
                    return {
                        "content": full_response,
                        "type": "mcp_response",
                        "query": user_query
                    }
                else:
                    return {
                        "content": "No response received from MCP server",
                        "type": "error",
                        "query": user_query
                    }
                    
        except Exception as e:
            self.last_error = f"Error in MCP query: {str(e)}"
            logger.error(self.last_error)
            return None
    
    async def receive_from_mcp(self):
        """
        Legacy method for compatibility - Receive streaming messages from OpenAI API
        
        This method simulates Server-Sent Events (SSE) handling by making a streaming
        request to the OpenAI API.
        
        Returns:
            dict: Parsed response or None if error
        """
        # Check connection state and reconnect if needed
        if not self.session or self.connection_state != ConnectionState.CONNECTED:
            connected = await self.connect_to_mcp()
            if not connected:
                logger.error(f"Failed to establish connection to OpenAI API. Last error: {self.last_error}")
                return None
        
        chat_endpoint = self.openai_api_url
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
            async with self.session.post(chat_endpoint, json=simple_message, headers=self.openai_headers) as response:
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
            """Async function to process messages with MCP server"""
            try:
                # Connect to MCP server if not connected
                if not self.session or self.connection_state != ConnectionState.CONNECTED:
                    connected = await self.connect_to_mcp()
                    if not connected:
                        logger.error(f"Failed to connect to MCP server: {self.last_error}")
                        return f"Error: Failed to connect to MCP server. {self.last_error}"

                # Process the last message
                last_message = messages[-1]["content"]
                
                # Check if this is a question that should be handled by the MCP server
                if last_message and "?" in last_message:
                    logger.info("Identified user question, querying MCP server...")
                    # Use query_mcp for questions
                    mcp_response = await self.query_mcp(last_message)
                    if mcp_response:
                        return mcp_response.get("content", "No response from MCP server")
                    else:
                        logger.warning("MCP query failed, falling back to OpenAI API")
                
                # Fall back to OpenAI if MCP query fails or if it's not a question
                logger.info("Using OpenAI API for response")
                # Send to OpenAI API and get response
                api_response = await self.send_to_mcp({
                    "model": "gpt-3.5-turbo",
                    "system": self.system_message,
                    "content": last_message,
                    "sender": sender.name if sender else "unknown"
                })

                if api_response:
                    return api_response.get("content", "No response from OpenAI API")
                return f"Failed to get response. Last error: {self.last_error}"
            finally:
                # We don't close the connection here to allow for reuse
                # It will be closed when the agent is destroyed or explicitly closed
                pass

        # Run the async function in the event loop
        try:
            # Define a synchronous function to handle running the async function
            def run_in_new_loop():
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(new_loop)
                    # Store the loop so we don't recreate it unnecessarily
                    self.event_loop = new_loop
                    # Run the async function with timeout in the new loop
                    return new_loop.run_until_complete(
                        asyncio.wait_for(process_with_mcp(), timeout=60)
                    )
                except asyncio.TimeoutError:
                    logger.error("Operation timed out after 60 seconds")
                    return "Request timed out. Please try again later."
                except asyncio.CancelledError:
                    logger.error("Operation was cancelled")
                    return "Request was cancelled. Please try again."
                except Exception as e:
                    logger.error(f"Error in event loop: {str(e)}")
                    raise e
                finally:
                    # Don't close the loop here to avoid "Event loop is closed" errors
                    # But do clean up any pending tasks to prevent resource leaks
                    for task in asyncio.all_tasks(new_loop):
                        if not task.done() and task != asyncio.current_task(new_loop):
                            task.cancel()
                    # Optionally, we could run the loop a bit longer to let tasks cleanup
                    # new_loop.run_until_complete(asyncio.sleep(0.1))
                    pass

            # Check if we're already in an async context
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                logger.debug("Found existing event loop, using run_in_executor")
                
                # We're in an async context, which is trickier
                # Using run_in_executor to run our sync function in a separate thread
                # This avoids the "Timeout context manager should be used inside a task" error
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_response = loop.run_in_executor(executor, run_in_new_loop)
                    # Get the result from the future
                    response = future_response.result()
                    logger.debug("Successfully executed in separate thread")
                    
            except RuntimeError:
                # No running event loop
                logger.debug("No running event loop found")
                
                # Check if we have a previously created event loop that's still usable
                if hasattr(self, 'event_loop') and self.event_loop and not self.event_loop.is_closed():
                    logger.debug("Using existing cached event loop")
                    old_loop = asyncio.get_event_loop()
                    try:
                        # Set our stored event loop as the current one
                        asyncio.set_event_loop(self.event_loop)
                        # Run the async function with proper timeout handling
                        response = self.event_loop.run_until_complete(
                            asyncio.wait_for(process_with_mcp(), timeout=60)
                        )
                        logger.debug("Successfully executed in cached event loop")
                    except Exception as e:
                        logger.error(f"Error using existing event loop: {str(e)}")
                        # If there was an error with the cached loop, create a new one
                        logger.debug("Falling back to creating a new event loop")
                        try:
                            # Clean up any pending tasks in the old loop
                            for task in asyncio.all_tasks(self.event_loop):
                                if not task.done():
                                    logger.debug(f"Cancelling uncompleted task: {task}")
                                    task.cancel()
                            
                            # If the error was a timeout, inform the user
                            if isinstance(e, asyncio.TimeoutError):
                                response = "Request timed out. Please try again later."
                            else:
                                # Create a brand new loop since the cached one failed
                                response = run_in_new_loop()
                        except Exception as nested_e:
                            logger.error(f"Error in fallback handling: {str(nested_e)}")
                            response = f"An error occurred: {str(e)}, with fallback error: {str(nested_e)}"
                    finally:
                        # Restore the previous event loop setting
                        asyncio.set_event_loop(old_loop)
                else:
                    # Create a new event loop since we don't have a usable cached one
                    logger.debug("No usable cached event loop found, creating new one")
                    response = run_in_new_loop()
                    logger.debug("Successfully created and executed in new event loop")
        except asyncio.TimeoutError:
            logger.error("Request to OpenAI API timed out after 60 seconds")
            response = "Request timed out. Please try again later."
        except Exception as e:
            logger.error(f"Error processing OpenAI API request: {str(e)}")
            response = f"An error occurred while processing your request: {str(e)}"
        return response

    def __del__(self):
        """
        Ensure proper cleanup of resources when the agent is garbage collected
        """
        try:
            # Create a new event loop for cleanup if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Close the session
            if hasattr(self, 'session') and self.session and not self.session.closed:
                if not loop.is_closed():
                    try:
                        loop.run_until_complete(self._close_session())
                    except Exception as e:
                        logger.error(f"Error cleaning up session in __del__: {str(e)}")

            # Clean up event loop
            if hasattr(self, 'event_loop') and self.event_loop and not self.event_loop.is_closed():
                try:
                    # Cancel any running tasks
                    for task in asyncio.all_tasks(self.event_loop):
                        if not task.done():
                            task.cancel()
                except Exception as e:
                    logger.error(f"Error cleaning up tasks in __del__: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in __del__ cleanup: {str(e)}")

# Example usage
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
    # Create an MCP agent
    mcp_agent = MCPAgent(
        name="MCP_Agent",
        system_message="I am an MCP agent that connects to Neon's database knowledge platform. I can answer questions about Neon databases and PostgreSQL.",
        mcp_server_url="https://mcp.neon.tech/sse",  # Explicitly set MCP server URL
        neon_api_key=os.getenv("NEON_API_KEY"),  # Explicitly get Neon API key
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
        message="I need information about Neon databases. Can you help me with that?"
    )

    # Note: Make sure to set NEON_API_KEY in your .env file to use MCP functionality
    # Example:
    # NEON_API_KEY=neon_api_23abc456def789ghi0jklmno  # Neon API keys start with "neon_"
    # OPENAI_API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz  # OpenAI API keys start with "sk-"
    # MCP_SERVER_URL=https://mcp.neon.tech/sse
    #
    # Important notes:
    # 1. Neon API keys must start with "neon_" prefix
    # 2. Do not include "Bearer" in your .env file - that's added automatically in the code
    # 3. Make sure there are no extra spaces or quotes in your .env file
    # 4. MCP connection issues are often related to invalid API keys
