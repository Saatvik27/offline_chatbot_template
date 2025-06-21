import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
from docx import Document
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
from datetime import datetime

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document processing, embedding generation, and vector storage."""
    
    def __init__(self):
        self.config = Config()
        self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
        )
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """Initialize ChromaDB vector database."""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.CHROMA_DB_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Vector database initialized: {self.config.CHROMA_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from supported file formats."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_extension}")
            return ""
    
    def process_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents and store embeddings."""
        results = {
            "processed": 0,
            "failed": 0,
            "total_chunks": 0,
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                # Extract text
                text = self.extract_text_from_file(file_path)
                if not text:
                    results["failed"] += 1
                    results["errors"].append(f"No text extracted from {file_path}")
                    continue
                
                # Split into chunks
                chunks = self.text_splitter.split_text(text)
                if not chunks:
                    results["failed"] += 1
                    results["errors"].append(f"No chunks created from {file_path}")
                    continue
                
                # Generate embeddings and store
                self._store_document_chunks(
                    chunks=chunks,
                    source_file=file_path,
                    metadata={
                        "source": os.path.basename(file_path),
                        "file_path": file_path,
                        "processed_at": datetime.now().isoformat(),
                        "chunk_count": len(chunks)
                    }
                )
                
                results["processed"] += 1
                results["total_chunks"] += len(chunks)
                logger.info(f"Processed {file_path}: {len(chunks)} chunks")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error processing {file_path}: {str(e)}")
                logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def _store_document_chunks(self, chunks: List[str], source_file: str, metadata: Dict):
        """Store document chunks with embeddings in vector database."""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # Prepare data for storage
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_text": chunk[:200] + "..." if len(chunk) > 200 else chunk
                })
                metadatas.append(chunk_metadata)
            
            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
        except Exception as e:
            logger.error(f"Error storing chunks for {source_file}: {e}")
            raise
    
    def search_similar_documents(self, query: str, k: int = None) -> List[Dict]:
        """Search for similar documents using vector similarity."""
        if k is None:
            k = self.config.RETRIEVAL_K
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": 1 - distance,  # Convert distance to similarity
                        "rank": i + 1
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.config.COLLECTION_NAME,
                "embedding_model": self.config.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "error": str(e)}
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection(name=self.config.COLLECTION_NAME)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
