import os
from typing import Dict, List, Optional
import logging
import numpy as np
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from autogen_agentchat.tools import BaseTool


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory where PDF files are stored
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdfs")
# Directory where vector stores will be saved
VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_stores")

# Create directories if they don't exist
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)


class PDFKnowledgeBase:
    def __init__(self, company: str, pdf_filename: str = None):
        """Initialize the PDF knowledge base for a specific company.

        Args:
            company: The company name (e.g., "microsoft" or "samsung")
            pdf_filename: Optional specific PDF filename, otherwise use "{company}_data.pdf"
        """
        self.company = company.lower()
        self.pdf_filename = pdf_filename or f"{self.company}_data.pdf"
        self.pdf_path = os.path.join(PDF_DIR, self.pdf_filename)
        self.vector_store_path = os.path.join(VECTOR_DIR, f"{self.company}_store")

        # Check if the PDF file exists
        if not os.path.exists(self.pdf_path):
            logger.error(f"PDF file not found: {self.pdf_path}")
            raise FileNotFoundError(f"PDF file for {company} not found at {self.pdf_path}")

        # Initialize Gemini embedding model
        api_key = "AIzaSyC5ePg-ZsJfgePj7mTZxKglfuKGhPOmChU"
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

        # Create or load the vector store
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Create a new vector store or load an existing one."""
        # Check if vector store already exists
        if os.path.exists(self.vector_store_path) and os.path.isdir(self.vector_store_path):
            logger.info(f"Loading existing vector store for {self.company}")
            try:
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings
                )
                return
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}. Creating a new one.")

        # Create a new vector store
        logger.info(f"Creating new vector store for {self.company}")
        try:
            # Load the PDF
            loader = PyPDFLoader(self.pdf_path)
            documents = loader.load()

            # Split the text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_documents(documents)

            # Create the vector store
            self.vector_store = FAISS.from_documents(texts, self.embeddings)

            # Save the vector store
            self.vector_store.save_local(self.vector_store_path)
            logger.info(f"Vector store created and saved for {self.company}")
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise

    def query(self, question: str, k: int = 5) -> str:
        """Query the knowledge base with a question.

        Args:
            question: The question to ask
            k: Number of most relevant documents to retrieve

        Returns:
            A formatted string with the most relevant information
        """
        try:
            # Search for the most relevant documents
            docs = self.vector_store.similarity_search(question, k=k)

            # Format the results
            results = [f"Document {i + 1}:\n{doc.page_content}\n" for i, doc in enumerate(docs)]

            return "\n".join(results)
        except Exception as e:
            logger.error(f"Error querying the knowledge base: {e}")
            return f"Error retrieving information from {self.company} knowledge base."

    def get_company_overview(self) -> str:
        """Get a general overview of the company's products and services.

        Returns:
            A formatted string with company overview information
        """
        return self.query("What are the main products, services, and business areas of this company?")

    def get_product_information(self) -> str:
        """Get detailed information about the company's products.

        Returns:
            A formatted string with product information
        """
        return self.query("List and describe the current products and their features.")

    def get_innovation_info(self) -> str:
        """Get information about the company's innovations and future directions.

        Returns:
            A formatted string with innovation information
        """
        return self.query("What are the company's recent innovations, R&D focus, and future directions?")


def get_company_data(company: str, query_type: str = "overview") -> str:
    """Get data for a specific company from its PDF.

    Args:
        company: The company name (microsoft or samsung)
        query_type: Type of query (overview, products, innovation)

    Returns:
        Formatted string with the requested information
    """
    try:
        kb = PDFKnowledgeBase(company)

        if query_type == "overview":
            return kb.get_company_overview()
        elif query_type == "products":
            return kb.get_product_information()
        elif query_type == "innovation":
            return kb.get_innovation_info()
        else:
            return kb.query(query_type)
    except FileNotFoundError:
        logger.error(f"PDF file for {company} not found.")
        return f"Error: PDF file for {company} not found. Please ensure you have a {company}_data.pdf file in the pdfs directory."
    except Exception as e:
        logger.error(f"Error getting {company} data: {str(e)}")
        return f"Error retrieving information for {company}: {str(e)}"


class CompanyDataTool(BaseTool):
    name: str = "get_company_data"
    description: str = "Get information about a company from its documentation"

    def __init__(self):
        super().__init__()

    def run(self, company: str, data_type: str = "overview") -> str:
        """
        Retrieve information about a company.

        Args:
            company: The company name (e.g., "microsoft" or "samsung")
            data_type: Type of data to retrieve (overview, products, innovation)

        Returns:
            Formatted string with the requested information
        """
        try:
            return get_company_data(company, data_type)
        except Exception as e:
            return f"Error retrieving {company} {data_type} data: {str(e)}"