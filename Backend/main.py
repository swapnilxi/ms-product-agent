from fastapi import FastAPI, BackgroundTasks

import os
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware  
from productAgent import run_agent as run_product_agent
from marketingAgent import run_agent as run_marketing_agent
from researchAgent import run_agent as run_research_agent
from agent_pipeline import research_to_marketing_flow



# Initialize FastAPI app
app = FastAPI()


# CORS settings for allowing cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin for now
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Simple root route to check the app
@app.get("/")
def root():
    return {"message": "Hello from FastAPI Lambda"}

# Endpoint for agent1
@app.get("/agent1")
def agent1():
    return {"agent": "Agent 1 triggered"}

# Endpoint for agent2
@app.get("/agent2")
def agent2():
    return {"agent": "Agent 2 triggered"}

# Endpoint for chat
@app.get("/chat")
def agent_chat():
    return {"message": "Agent chat triggered"}

@app.get("/product-agent")
async def product_agent(background_tasks: BackgroundTasks):
    """Trigger the product agent as a background task."""
    if ProductAgent is None:
        return {"status": "Product agent is not available. please check the modules"}
    
    background_tasks.add_task(ProductAgent.main)
    return {"status": "Product agent task started."}

@app.get("/research-agent")
async def research_agent(background_tasks: BackgroundTasks):
    """Trigger the research agent as a background task."""
    if researchAgent is None:
        return {"status": "Research agent is not available. please check the modules"}
    
    background_tasks.add_task(researchAgent.main)
    return {"status": "Research agent task started."}

@app.get("/marketing-agent")
async def marketing_agent(background_tasks: BackgroundTasks):
    """Trigger the marketing agent as a background task."""
    if marketingAgent is None:
        return {"status": "Marketing agent is not available. please check the modules"}
    
    background_tasks.add_task(marketingAgent.main)
    return {"status": "Marketing agent task started."}

@app.get("/run-pipeline")
async def run_pipeline():
    try:
        print("Pipeline task started...")
        await research_to_marketing_flow()
        print("✅ Pipeline task completed!")
        return {"status": "success"}
    except Exception as e:
        print("Error inside /run-pipeline:", e)
        return {"status": "error", "detail": str(e)}
        
# Endpoint to handle dynamic items
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
