from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile
import os
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config import Config
from document_processor import DocumentProcessor
from llm_handler import OfflineLLM

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Offline Chatbot API",
    description="A fast, deployable backend API for offline document-based and general chat",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = Config()
doc_processor = None
llm_handler = None
executor = ThreadPoolExecutor(max_workers=2)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    mode: str = "general"  # "general" or "document"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    mode: str
    processing_time: float
    conversation_id: str
    metadata: Dict[str, Any]

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    processed: int
    failed: int
    total_chunks: int
    errors: List[str] = []

class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    document_processor_available: bool
    total_documents: int
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global doc_processor, llm_handler
    
    try:
        # Initialize document processor
        doc_processor = DocumentProcessor()
        logger.info("Document processor initialized")
        
        # Initialize LLM handler
        llm_handler = OfflineLLM()
        logger.info("LLM handler initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Offline Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    ollama_available = False
    doc_processor_available = False
    total_documents = 0
    
    try:
        if llm_handler:
            model_status = llm_handler.check_model_availability()
            ollama_available = model_status.get("available", False)
        
        if doc_processor:
            doc_processor_available = True
            stats = doc_processor.get_collection_stats()
            total_documents = stats.get("total_chunks", 0)
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
    
    status = "healthy" if (ollama_available and doc_processor_available) else "degraded"
    
    return HealthResponse(
        status=status,
        ollama_available=ollama_available,
        document_processor_available=doc_processor_available,
        total_documents=total_documents,
        message="API is running"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for both general and document-based chat."""
    if not llm_handler:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    start_time = datetime.now()
    conversation_id = request.conversation_id or f"conv_{int(start_time.timestamp())}"
    
    try:
        # Run the potentially slow LLM operation in thread pool
        loop = asyncio.get_event_loop()
        
        if request.mode == "document":
            if not doc_processor:
                raise HTTPException(status_code=503, detail="Document processor not available")
            
            # Get relevant documents
            relevant_docs = await loop.run_in_executor(
                executor,
                doc_processor.search_similar_documents,
                request.message,
                config.RETRIEVAL_K
            )
            
            # Generate response with context
            llm_response = await loop.run_in_executor(
                executor,
                llm_handler.generate_response,
                request.message,
                relevant_docs
            )
            
            sources = list(set([
                doc.get("metadata", {}).get("source", "Unknown")
                for doc in relevant_docs
            ]))
            
        else:
            # General chat - no document context
            llm_response = await loop.run_in_executor(
                executor,
                llm_handler.generate_response,
                request.message,
                None
            )
            relevant_docs = []
            sources = []
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        metadata = {
            "model": llm_response.get("model", "Unknown"),
            "context_used": len(relevant_docs),
            "response_tokens": llm_response.get("response_tokens", 0),
            "sources": sources,
            "success": llm_response.get("success", False)
        }
        
        return ChatResponse(
            response=llm_response["response"],
            mode=request.mode,
            processing_time=processing_time,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/upload-documents", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents for document-based chat."""
    if not doc_processor:
        raise HTTPException(status_code=503, detail="Document processor not available")
    
    try:
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files
            for file in files:
                if file.size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File {file.filename} too large (max {config.MAX_FILE_SIZE_MB}MB)"
                    )
                
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                file_paths.append(file_path)
            
            # Process documents in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                executor,
                doc_processor.process_documents,
                file_paths
            )
            
            return DocumentUploadResponse(
                success=results["processed"] > 0,
                message=f"Processed {results['processed']} documents successfully",
                processed=results["processed"],
                failed=results["failed"],
                total_chunks=results["total_chunks"],
                errors=results["errors"]
            )
            
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.delete("/documents")
async def clear_documents():
    """Clear all processed documents."""
    if not doc_processor:
        raise HTTPException(status_code=503, detail="Document processor not available")
    
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, doc_processor.clear_collection)
        return {"message": "All documents cleared successfully"}
    
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear documents: {str(e)}")

@app.get("/documents/stats")
async def get_document_stats():
    """Get statistics about processed documents."""
    if not doc_processor:
        raise HTTPException(status_code=503, detail="Document processor not available")
    
    try:
        stats = doc_processor.get_collection_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Document stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document stats: {str(e)}")

@app.get("/models")
async def get_available_models():
    """Get available Ollama models."""
    if not llm_handler:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    try:
        model_info = llm_handler.check_model_availability()
        return model_info
    
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
