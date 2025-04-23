from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from agent1 import agent, model_client  # Import your agent and model client

app = FastAPI()

# Configure CORS (adjust as needed for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    query: str
    company: Union[str, None] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/query-agent")
async def query_agent(request: AgentRequest):
    try:
        # Create the task string based on the request
        task = request.query
        if request.company:
            task = f"What are products available at {request.company}?"
        
        # Run the agent and get the response
        response = await agent.run_stream(task=task)
        
        # Process the response (you might need to adjust this based on your agent's response format)
        if hasattr(response, 'content'):
            return {"response": response.content}
        return {"response": str(response)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    await model_client.close()