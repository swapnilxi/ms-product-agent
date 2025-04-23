import requests

# Test the agent endpoint
response = requests.post(
    "http://localhost:8000/query-agent",
    json={"query": "Tell me about products", "company": "Google"}
)
print(response.json())