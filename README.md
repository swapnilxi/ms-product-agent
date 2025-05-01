The list of 8 agents working togther, as 3 teams
- Research agent
- Product collabration agent
- Marketing Plan agent

colabgen-report-links: https://drive.google.com/drive/folders/1iFzSJ8_4jZUz22yva-jlL2CUQL9bq0KK?usp=sharing

video demo - https://streamyard.com/23za4m5wbj8d

Deployed UI- https://happy-bay-02a0aa40f.6.azurestaticapps.net/

Deployed BackendUrl - http://fastapiaci123.centralus.azurecontainer.io:8003/docs#/default/research_agent_research_agent_get_get

in the end it will give you beautiful report with properly fromatted data  and  action plan

Multi-AI Agent Collaboration System – Hackathon Submission
This project showcases a coordinated system of autonomous AI agents working together to simulate real-world cross-functional collaboration between companies and internal teams. Each agent operates with a clear responsibility—ranging from industry-specific research to innovation planning, market strategy, and executive reporting.

The system demonstrates how distributed intelligence can streamline complex workflows and accelerate decision-making in enterprise environments.

Agent Overview:
Agent 1 & Agent 2:
Representing Company 1 and Company 2 respectively, for example, Microsoft as Company 1 and Samsung as Company 2 and vice versa. These agents gather company-specific insights, product developments, and competitive intelligence.

Agent 3:
Focuses on identifying innovative opportunities and extracting unique selling propositions (USPs) from the combined research findings.

Agent 4:
Acts as the review and summarization unit, distilling relevant insights and storing them for future reference and reuse.

Agent 5 & Agent 6:
Conduct market research and analyze sales data across regions, then formulate high-performing country-specific marketing strategies.

Agent 7:
Compiles dashboard-level summaries for senior management and integrates with customer support systems for real-time interaction.


### Instruction for Running the backend 

# FastAPI Dockerized App

This is a Dockerized FastAPI backend application. Follow the instructions below to build and run it locally using Docker.

---

## 🐳 Running the FastAPI App with Docker (Local Development)

### ✅ Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git
- (Optional) Docker Buildx (already included in Docker Desktop for macOS/Windows)

---

### 📦 Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/your-fastapi-app.git
cd your-fastapi-app
```

---

### 🛠 Step 2: Build the Docker Image

#### Option A: On Apple Silicon (M1/M2/M3 Macs)

To ensure compatibility with cloud platforms like Azure (which use `amd64`):

```bash
docker buildx create --use  # Only once if not already done
docker buildx build --platform linux/amd64 -t fastapi-local --load .
```

#### Option B: On Intel-based Macs or Linux/Windows

```bash
docker build -t fastapi-local .
```

---

### 🚀 Step 3: Run the Container

#### Run with default port (8003):

```bash
docker run -p 8003:8003 fastapi-local
```

#### Or bind to another local port (e.g., 8080):

```bash
docker run -p 8080:8003 fastapi-local
```

---

### 🌐 Step 4: Access the API

Once the container is running, open your browser:

- Default route: [http://localhost:8003](http://localhost:8003)
- API docs (Swagger UI): [http://localhost:8003/docs](http://localhost:8003/docs)
- you can use frontend url for ease acess : [Deployed UI](https://happy-bay-02a0aa40f.6.azurestaticapps.net/)

*If using a different port, adjust URLs accordingly.*

---

### 🧪 Optional: Run Without Docker (for local debugging)

```bash
pip install -r requirements.txt
```
```
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```
or 
```
python main.py
```

---

### 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| `localhost refused to connect` | Make sure the container is running with `docker ps`. |
| Port already in use | try to use :8003 as frontend can read that on your local (`-p 8080:8003`) |
| No response from app | Check logs with `docker logs <container-id>` |
| Docker DNS issues | Restart Docker Desktop or try `docker system prune` |

---

### 📁 Project Structure (Example)

```
Backend/
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

