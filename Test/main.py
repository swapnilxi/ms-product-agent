from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from autogen import ConversableAgent
import autogen
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/")
async def read_index():
    return FileResponse("index.html")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents (this will happen once when the server starts)
config_list_gemini = autogen.config_list_from_json("model_config.json")

# Configure the agents
SYSTEM_MESSAGE_INITIAL_PRODUCT_DESCRIBER = """
Your task is to create compelling, accurate descriptions for Microsoft products. 
Generate the following elements for the product description:
- Product Name
- Key Features
- Target Audience
- Value Proposition
- Technical Specifications (when applicable)

Guidelines to follow:
- Maintain accuracy about Microsoft's products
- Highlight Microsoft-specific differentiators
- Use professional but approachable language
- Emphasize integration with other Microsoft products
- Include relevant technical details for technical products
- Output in markdown format
"""

SYSTEM_MESSAGE_PRODUCT_DESCRIBER = """
Review the feedback and improve the product description while keeping the accurate parts.
Retain the elements that are already strong.
If there's no actionable feedback, output the final description.
"""

SYSTEM_MESSAGE_PRODUCT_REVIEWER = """
As a Microsoft product expert, review this product description for:
- Technical accuracy about Microsoft products
- Clarity of value proposition
- Appropriate level of technical detail
- Clear identification of target audience
- Highlighting of Microsoft ecosystem advantages
- Competitive differentiation

Provide specific, actionable feedback to improve the description.
Note what's working well and should be kept.
Do not rewrite the description - only provide feedback.
"""

# Initialize agents
initial_product_describer = ConversableAgent(
    name="Microsoft Product Describer",
    system_message=SYSTEM_MESSAGE_INITIAL_PRODUCT_DESCRIBER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None
)
product_describer = ConversableAgent(
    name="Microsoft Product Describer",
    system_message=SYSTEM_MESSAGE_PRODUCT_DESCRIBER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None
)

product_reviewer = ConversableAgent(
    name="Microsoft Product Reviewer",
    system_message=SYSTEM_MESSAGE_PRODUCT_REVIEWER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None
)


product_marketer = ConversableAgent(
    name="Microsoft Product MArketer",
    system_message=SYSTEM_MESSAGE_PRODUCT_REVIEWER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None
)

class ProductDescriptionRequest(BaseModel):
    product_idea: str
    max_turns: int = 2  # default value

@app.post("/generate-product-description/")
async def generate_product_description(request: ProductDescriptionRequest):
    try:
        # Initial description generation
        initial_description_reply = initial_product_describer.generate_reply(
            messages=[{"content": request.product_idea, "role": "user"}]
        )

        # Start the chat between describer and reviewer
        chat_result = product_describer.initiate_chat(
            product_reviewer,
            message="Here's a Microsoft product that needs a description: \n" 
            + initial_description_reply["content"],
            max_turns=request.max_turns
        )

        # Extract the final message (last message from the chat)
        final_message = chat_result.chat_history[-1]["content"]

        return {
            "status": "success",
            "initial_description": initial_description_reply["content"],
            "final_description": final_message,
            "chat_history": chat_result.chat_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)