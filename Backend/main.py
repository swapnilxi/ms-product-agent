from fastapi import FastAPI, BackgroundTasks

import os
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  
from productAgent import run_agent_post as run_product_agent
from researchAgent import run_agent_post as run_research_agent
from marketingAgent import run_agent_post as run_marketing_agent
from productAgent import run_agent as run_product_agent_get
from marketingAgent import run_agent as run_marketing_agent_get
from researchAgent import run_agent as run_research_agent_get
from agent_pipeline import run_full_pipeline
from save_report import list_reports, get_report_path, delete_report, save_pipeline_report
from fastapi.responses import FileResponse
from typing import Optional


# Initialize FastAPI app
app = FastAPI()

# Define the input model
class AgentInput(BaseModel):
    companyName1: str
    companyName2: str
    textInstruction: Optional[str] = None  
    task: Optional[str] = None  
    
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
    return {"message": "Hello from FastAPI!"}

#research agent
@app.post("/research-agent")
async def research_agent_dynamic(input: AgentInput):
    chat_result = await run_research_agent(
        company1=input.companyName1,
        company2=input.companyName2,
        user_input=input.textInstruction,
        task=input.task 
    )
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }

@app.post("/product-agent")
async def product_agent_dynamic(input: AgentInput):
    chat_result = await run_product_agent(
        company1=input.companyName1,
        company2=input.companyName2,
        user_input=input.textInstruction,
        task=input.task 
    )
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }

@app.post("/marketing-agent")
async def marketing_agent_dynamic(input: AgentInput):
    chat_result = await run_marketing_agent(
        company1=input.companyName1,
        company2=input.companyName2,
        user_input=input.textInstruction,
        task=input.task 
    )
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }

#get api enpooints
@app.post("/run-pipeline")
async def run_pipeline_dynamic(input: AgentInput):
    try:
        print("Dynamic Pipeline started...")

        results = await run_full_pipeline(
            company1=input.companyName1,
            company2=input.companyName2,
            user_input=input.textInstruction
        )

        print("✅ Dynamic Pipeline completed!")

        role_mapping = {
            "research_output": "research_agent",
            "product_output": "product_agent",
            "marketing_output": "marketing_agent"
        }

        messages = [
            {
                "role": role_mapping[key],
                "stage": key.replace("_", " ").title(),
                "content": value
            }
            for key, value in results.items()
        ]


        markdown_report = save_pipeline_report(results)

        return {"status": "success", 
                "messages": messages,
                "markdown_report":markdown_report, 
                }

    except Exception as e:
        print("Error in dynamic pipeline:", e)
        return {"status": "error", "detail": str(e)}




# Standalone - Run Research Agent
@app.get("/research-agent-test")
async def research_agent_status(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_research_agent_get)
    return {"status": "Research agent task started."}

@app.get("/research-agent-get")
async def research_agent():
    chat_result = await run_research_agent_get()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }

# Standalone - Run Product Agent
@app.get("/product-agent-get")
async def product_agent():
    chat_result = await run_product_agent_get()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }
    
# Standalone - Run Marketing Agent
@app.get("/marketing-agent-get")
async def marketing_agent():
    chat_result = await run_marketing_agent_get()
    return {
        "status": "success",
        "messages": [
            {"source": msg.source, "content": msg.content}
            for msg in chat_result.messages
        ]
    }
# Full pipeline
@app.get("/run-pipeline-get")
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
        print("Error in pipeline:", e)
        return {"status": "error", "detail": str(e)}

# List all reports
@app.get("/get-reports")
def get_reports():
    try:
        reports = list_reports()
        return {"status": "success", "reports": reports}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Download specific report
@app.get("/download-report/{filename}")
def download_report(filename: str):
    try:
        report_path = get_report_path(filename)
        if report_path:
            return FileResponse(report_path, media_type="text/markdown", filename=filename)
        else:
            return {"status": "error", "detail": "Report not found."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
#save report-pdf -- moved this on frontend
@app.get("/download-report-pdf/{filename}")
def download_pdf(filename: str):
    file_path = os.path.join("reports", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    return {"status": "error", "detail": "PDF not found"}


#delete specific report
@app.delete("/delete-report/{filename}")
def delete_report_endpoint(filename: str):
    try:
        deleted = delete_report(filename)
        if deleted:
            return {"status": "success", "message": f"{filename} deleted."}
        else:
            return {"status": "error", "detail": "File not found."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    
# Example dynamic item endpoint
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Uvicorn entrypoint for local testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
