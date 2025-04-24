from fastapi import FastAPI
from mangum import Mangum
import os
from fastapi.middleware.cors import CORSMiddleware

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

# Endpoint to handle dynamic items
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Handler for AWS Lambda integration using Mangum
handler = Mangum(app)
