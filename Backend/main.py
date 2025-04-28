from fastapi import FastAPI, BackgroundTasks

import os
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware  
from productAgent import run_agent as run_product_agent
from marketingAgent import run_agent as run_marketing_agent
from researchAgent import run_agent as run_research_agent
from agent_pipeline import run_full_pipeline



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

# Root Route
@app.get("/")
def root():
    return {"message": "Hello from FastAPI Lambda"}

# Standalone - Run Research Agent
@app.get("/research-agent-test")
async def research_agent_status(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_research_agent)
    return {"status": "Research agent task started."}

@app.get("/research-agent")
async def research_agent():
    chat_result = await run_research_agent()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }

# Standalone - Run Product Agent
@app.get("/product-agent")
async def product_agent():
    chat_result = await run_product_agent()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }
    
# Standalone - Run Marketing Agent
@app.get("/marketing-agent")
async def marketing_agent():
    chat_result = await run_marketing_agent()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }
# Full pipeline
@app.get("/run-pipeline")
async def run_pipeline():
    try:
        print("🚀 Pipeline task started...")

        results = await run_full_pipeline()

        print("✅ Pipeline task completed!")

        # Prepare structured frontend-friendly output
        output = []
        for stage, content in results.items():
            output.append({
                "stage": stage.replace('_', ' ').title(),  # e.g., research_output -> Research Output
                "content": content
            })

        return {
            "status": "success",
            "pipeline_results": output
        }

    except Exception as e:
        print("❌ Error in pipeline:", e)
        return {"status": "error", "detail": str(e)}
    
# Example dynamic item endpoint
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Uvicorn entrypoint for local testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    





