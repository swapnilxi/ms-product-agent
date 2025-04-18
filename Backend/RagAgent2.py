from autogen import AssistantAgent, UserProxyAgent
import psycopg2
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Configuration
DB_URL = "postgresql://neondb_owner:npg_MkPJB0Nn4jvT@ep-tiny-sea-a8a53w5y-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
GEMINI_API_KEY = "AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU"
MODEL_NAME = "all-MiniLM-L6-v2"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class VectorDBRetrieveAgent(UserProxyAgent):
    def __init__(self, db_url, **kwargs):
        super().__init__(**kwargs)
        self.db_url = db_url
        self.embedding_model = SentenceTransformer(MODEL_NAME)
        
    def retrieve_docs(self, query: str, n_results: int = 3, similarity_threshold: float = 0.8):
        """Custom retrieval using Sentence Transformers and Postgres"""
        # Generate embedding
        embedding = self.embedding_model.encode(query).tolist()
        
        # Query Postgres
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT content, 1 - (embedding <=> %s) as similarity
            FROM documents
            WHERE 1 - (embedding <=> %s) > %s
            ORDER BY similarity DESC
            LIMIT %s
        """, (embedding, embedding, similarity_threshold, n_results))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"content": r[0], "similarity": float(r[1])} for r in results]

def get_answer(question):
    """
    AutoGen QA system with Sentence Transformers and Postgres
    """
    # Configure LLM with an available model
    config_list = [{
        'model': 'available-model-id',  # Replace with a valid model ID
        'api_type': 'google',
        'api_key': GEMINI_API_KEY
    }]
    
    # Create agents
    assistant = AssistantAgent(
        name="assistant",
        llm_config={
            "config_list": config_list,
            "temperature": 0.7
        }
    )
    
    retriever = VectorDBRetrieveAgent(
        db_url=DB_URL,
        name="retriever",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=2,
        code_execution_config={"use_docker": False}  # Disable Docker requirement
    )
    
    # Initiate chat
    retriever.initiate_chat(
        assistant,
        message=question,
        search_string="",
        silent=True
    )
    
    return retriever.last_message(assistant)["content"]

if __name__ == "__main__":
    while True:
        question = input("\nEnter your question (or 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        print("\nSearching...")
        answer = get_answer(question)
        print(f"\nANSWER: {answer}")