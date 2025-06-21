import os
from typing import Optional

class Config:
    """Configuration settings for the offline chatbot."""
    
    # Database settings
    CHROMA_DB_PATH = "./chroma_db"
    COLLECTION_NAME = "document_embeddings"
      # Model settings
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "llama3.1:8b"  # Best model for document Q&A
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # Document processing
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_FILE_SIZE_MB = 10
    
    # Retrieval settings
    RETRIEVAL_K = 5  # Number of relevant chunks to retrieve
    SIMILARITY_THRESHOLD = 0.7
    
    # UI settings
    PAGE_TITLE = "Offline Chatbot"
    PAGE_ICON = "🤖"
    SIDEBAR_TITLE = "Document Management"
    
    # Supported file types
    SUPPORTED_FILE_TYPES = ['.pdf', '.docx', '.txt']
    
    # Security settings
    ENABLE_FILE_VALIDATION = True
    MAX_DOCUMENTS = 100
    
    @classmethod
    def get_ollama_url(cls) -> str:
        """Get the Ollama base URL."""
        return cls.OLLAMA_BASE_URL
    
    @classmethod
    def get_upload_path(cls) -> str:
        """Get the path for uploaded documents."""
        upload_path = "./uploaded_docs"
        os.makedirs(upload_path, exist_ok=True)
        return upload_path
