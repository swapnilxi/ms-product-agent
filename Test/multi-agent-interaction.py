
from autogen import ConversableAgent
import autogen

# Configure Gemini models
config_list_gemini = autogen.config_list_from_json("model_config.json")

SYSTEM_MESSAGE_INITIAL_CFP_WRITER = """
Your task is to write a good, clean, and impactful proposal or submission for a CFP to a technical event. 
Generate only the following as part of the CFP:
- Title
- Abstract
- Key Takeaways
The following are key tenets you have to abide by:
- Stay true to the original idea or intent of the author
- Do not add in your own ideas or details that the author has not provided and do not try to elaborate on any technology
- Only rewrite the idea expressed by the author in the form of a well-structured and impactful talk proposal
- Make it technical, concise, crisp, and impactful. Output the proposal in a markdown format.
"""
initial_cfp_writer = ConversableAgent(
    name="CFP Writer",
    system_message=SYSTEM_MESSAGE_INITIAL_CFP_WRITER,
    llm_config = {"config_list" : config_list_gemini},
    code_execution_config = False,
    human_input_mode = "NEVER",
    function_map = None
)

SYSTEM_MESSAGE_CFP_WRITER = """
Check if there are any improvement points, and use it to improve the submission. 
Retain the points that are good and doesn't need to be changed. 
If there is no actionable feedback, then output the final submission.
"""

cfp_writer = ConversableAgent(
    name="CFP Writer",
    system_message=SYSTEM_MESSAGE_CFP_WRITER,
    llm_config = {"config_list" : config_list_gemini},
    code_execution_config = False,
    human_input_mode = "NEVER",
    function_map = None
)


SYSTEM_MESSAGE_CFP_REVIEWER = """
Your task is to review a submission for a technical talk.
The talk will have the following details:
- Title
- Abstract
- Key Takeaways
Review the submissions for the following:
- Clarity of thought and crisp writeup
- Showcasing value to the audience who will attend the talk
- Easy to understand what this talk is about
- Being specific about the technologies being used and why they are being used
- Clear takeaways for the audience
- Clarity on who is the Intended audience
Keeping these tenets in mind, you will review the submission and provide precise and concise, actionable feedback, that will help improve the submission.
You should not write or re-write the submission or any parts of it.
Provide clear and concise feedback that the author can work on to improve on their writeup.
If there are aspects that are good, mention them so that it can be retain and left unchanged.
"""
cfp_reviewer = ConversableAgent(
    name="CFP Reviewer",
    system_message=SYSTEM_MESSAGE_CFP_REVIEWER,
    llm_config = {"config_list" : config_list_gemini},
    code_execution_config = False,
    human_input_mode = "NEVER",
    function_map = None
)

# Initial CFP Generation
initial_cfp_generation_reply = initial_cfp_writer.generate_reply(
    messages=[{"content": "I would like to submit a CFP for a talk on multi-agents. These agents will use the Agentic framework and Gemini models", 
               "role": "user"}])

cfp_writer.initiate_chat(cfp_reviewer,
                         message="Following is a rough idea for which I would like a talk proposal that I can submit: \n" 
                         + initial_cfp_generation_reply["content"], max_turns=2)



# # How to Test and Post to Your FastAPI CFP Generator

# Here's a complete guide to testing your FastAPI CFP generation service, including different methods you can use.

# ## 1. Start Your FastAPI Server

# First, make sure your server is running:

# ```bash
# uvicorn main:app --reload
# ```

# This will start the server at `http://127.0.0.1:8000` with auto-reload enabled for development.

# ## 2. Testing Methods

# ### Method 1: Using FastAPI's Built-in Docs (Recommended for Development)

# 1. Open your browser and go to: `http://127.0.0.1:8000/docs`
# 2. You'll see Swagger UI documentation for your API
# 3. Find the `/generate-cfp/` endpoint and click "Try it out"
# 4. Enter your request JSON, for example:
# ```json
# {
#   "idea": "I want to talk about building multi-agent systems using AutoGen and Gemini models",
#   "max_turns": 2
# }
# ```
# 5. Click "Execute" to send the request
# 6. View the response in the UI

# ### Method 2: Using cURL (Command Line)

# ```bash
# curl -X POST "http://127.0.0.1:8000/generate-cfp/" \
# -H "Content-Type: application/json" \
# -d '{"idea": "I want to talk about building multi-agent systems using AutoGen and Gemini models", "max_turns": 2}'
# ```

# ### Method 3: Using Python (with requests library)

# Create a test script `test_api.py`:

# ```python
# import requests
# import json

# url = "http://127.0.0.1:8000/generate-cfp/"
# data = {
#     "idea": "I want to talk about building multi-agent systems using AutoGen and Gemini models",
#     "max_turns": 2
# }

# response = requests.post(url, json=data)

# print("Status Code:", response.status_code)
# print("Response:")
# print(json.dumps(response.json(), indent=2))
# ```

# Run it with:
# ```bash
# python test_api.py
# ```

# ### Method 4: Using Postman or Insomnia

# 1. Create a new POST request to `http://127.0.0.1:8000/generate-cfp/`
# 2. Set the header:
#    - `Content-Type: application/json`
# 3. Add the request body (raw JSON):
# ```json
# {
#   "idea": "I want to talk about building multi-agent systems using AutoGen and Gemini models",
#   "max_turns": 2
# }
# ```
# 4. Send the request and view the response

# ## 3. Expected Response

# A successful response will look something like this:

# ```json
# {
#   "status": "success",
#   "initial_proposal": "## Title\n\nBuilding Multi-Agent Systems with AutoGen and Gemini Models\n\n...",
#   "final_proposal": "## Title\n\nBuilding Multi-Agent Systems with AutoGen and Gemini Models\n\n...",
#   "chat_history": [
#     {
#       "content": "...",
#       "role": "assistant"
#     },
#     {
#       "content": "...",
#       "role": "user"
#     }
#   ]
# }
# ```

# ## 4. Testing the Health Check

# You can always test the health endpoint:

# ```bash
# curl "http://127.0.0.1:8000/health"
# ```
# or visit `http://127.0.0.1:8000/health` in your browser.

# ## 5. Testing Different Scenarios

# Try testing with:
# - Different talk ideas
# - Different max_turns values (1, 2, 3)
# - Empty or very short ideas to test error handling
# - Very long ideas to test performance

# ## 6. Production Testing

# When deployed to production, just replace `http://127.0.0.1:8000` with your production URL in all the examples above.

# This gives you multiple ways to test your API during development and after deployment. The built-in docs (Method 1) are particularly convenient during development.