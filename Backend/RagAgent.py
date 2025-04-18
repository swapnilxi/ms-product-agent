import os
import asyncio
from pathlib import Path
import re
from typing import List, Optional
import numpy as np

import aiofiles
import aiohttp
import asyncpg
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
from autogen_ext.models.openai import OpenAIChatCompletionClient
from openai import AsyncOpenAI

# Configuration - Use your Neon connection string here
import os
import asyncio
import re
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

import aiofiles
import aiohttp
import asyncpg
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Configuration - Use your Neon connection string
POSTGRES_DSN = "postgresql://neondb_owner:npg_MkPJB0Nn4jvT@ep-tiny-sea-a8a53w5y-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

class FreeEmbeddingModel:
    """Local embedding model using sentence-transformers"""
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    async def get_embedding(self, text: str) -> List[float]:
        # Run in thread pool to avoid blocking event loop
        embedding = await asyncio.to_thread(self.model.encode, text)
        return embedding.tolist()

class PostgreSQLVectorMemory(Memory):
    """PostgreSQL vector memory with free embeddings"""
    
    def __init__(self, table_name: str = "autogen_memory", k: int = 3, score_threshold: float = 0.4):
        self.table_name = table_name
        self.k = k
        self.score_threshold = score_threshold
        self.pool: Optional[asyncpg.Pool] = None
        self.embedding_model = FreeEmbeddingModel()

    async def connect(self):
        """Initialize database connection"""
        self.pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)
        
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR(384), -- Dimension for all-MiniLM-L6-v2
                    mime_type TEXT,
                    metadata JSONB
                )
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
            """)


    async def query(self, query: str) -> List[MemoryContent]:
        """Query memory (alias for search)"""
        return await self.search(query)

    async def update_context(self, context: dict) -> None:
        """Update context (not implemented for this memory type)"""
        pass
    
    async def add(self, content: MemoryContent):
        """Add content to memory"""
        embedding = await self.embedding_model.get_embedding(content.content)
        vector_str = f"[{','.join(map(str, embedding))}]"
        
        # Convert metadata dict to JSON string
        import json
        metadata_json = json.dumps(content.metadata)
        
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.table_name} (content, embedding, mime_type, metadata)
                VALUES ($1, $2, $3, $4)
            """, content.content, vector_str, content.mime_type.value, metadata_json)

    async def search(self, query: str) -> List[MemoryContent]:
        """Search similar content"""
        query_embedding = await self.embedding_model.get_embedding(query)
        
        async with self.pool.acquire() as conn:
            results = await conn.fetch(f"""
                SELECT content, mime_type, metadata, 1 - (embedding <=> $1) as similarity
                FROM {self.table_name}
                WHERE 1 - (embedding <=> $1) > $2
                ORDER BY similarity DESC
                LIMIT $3
            """, np.array(query_embedding).astype(np.float32), self.score_threshold, self.k)
            
        return [
            MemoryContent(
                content=r['content'],
                mime_type=MemoryMimeType(r['mime_type']),
                metadata=json.loads(r['metadata'])  # Deserialize JSON
            ) for r in results
        ]

    async def clear(self):
        """Clear all contents"""
        async with self.pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name}")

    async def close(self):
        """Cleanup resources"""
        if self.pool:
            await self.pool.close()

class SimpleDocumentIndexer:
    """Document indexer with chunking"""
    
    def __init__(self, memory: PostgreSQLVectorMemory, chunk_size: int = 1500):
        self.memory = memory
        self.chunk_size = chunk_size

    async def _fetch_content(self, source: str) -> str:
        """Fetch content from URL or file"""
        if source.startswith(("http://", "https://")):
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as response:
                    return await response.text()
        else:
            async with aiofiles.open(source, "r", encoding="utf-8") as f:
                return await f.read()

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r"<[^>]*>", " ", text)  # Remove HTML tags
        text = re.sub(r"\s+", " ", text)       # Collapse whitespace
        return text.strip()

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        return [text[i:i+self.chunk_size].strip() 
               for i in range(0, len(text), self.chunk_size)]

    async def index_documents(self, sources: List[str]) -> int:
        """Index multiple documents"""
        total_chunks = 0
        
        for source in sources:
            try:
                content = await self._fetch_content(source)
                cleaned = self._clean_text(content)
                
                for i, chunk in enumerate(self._chunk_text(cleaned)):
                    await self.memory.add(
                        MemoryContent(
                            content=chunk,
                            mime_type=MemoryMimeType.TEXT,
                            metadata={"source": source, "chunk_index": i}
                        )
                    )
                    total_chunks += 1
            except Exception as e:
                print(f"Error indexing {source}: {e}")
        
        return total_chunks

async def main():
    # Initialize memory systems
    doc_memory = PostgreSQLVectorMemory(table_name="documents", k=3)
    await doc_memory.connect()
    await doc_memory.clear()

    # Index sample documents
    indexer = SimpleDocumentIndexer(doc_memory)
    sources = [
        "https://raw.githubusercontent.com/microsoft/autogen/main/README.md",
        # Add other documentation URLs
    ]
    chunk_count = await indexer.index_documents(sources)
    print(f"Indexed {chunk_count} document chunks")

    # User preferences memory
    pref_memory = PostgreSQLVectorMemory(table_name="preferences", k=2)
    await pref_memory.connect()
    
    # Add preferences
    await pref_memory.add(MemoryContent(
        content="Always use metric units",
        mime_type=MemoryMimeType.TEXT,
        metadata={"category": "preferences", "type": "units"}
    ))

    # Initialize AI components
    # the `ChatCompletionClient` interface.
    model_client = OpenAIChatCompletionClient(
        model="gemini-1.5-flash-8b",
        api_key="AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU",    
    )
    
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        memory=[doc_memory, pref_memory],
        system_message="You are a helpful assistant that uses retrieved knowledge and user preferences, if you cannot find in your dataset fetch from Rag database"
    )

    # Example query
    stream = assistant.run_stream(task="What is desi chess factory?")
    await Console(stream)

    # Cleanup
    await model_client.close()
    await doc_memory.close()
    await pref_memory.close()

if __name__ == "__main__":
    asyncio.run(main())