import streamlit as st
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

# Import our custom modules
from config import Config
from document_processor import DocumentProcessor
from llm_handler import OfflineLLM

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #ff6b6b;
    }
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    .mode-indicator {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

class ChatbotApp:
    """Main Streamlit application for the offline chatbot."""
    
    def __init__(self):
        self.config = Config()
        self.initialize_session_state()
        self.doc_processor = self.get_doc_processor()
        self.llm_handler = self.get_llm_handler()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = {}
        
        if 'current_chat_mode' not in st.session_state:
            st.session_state.current_chat_mode = "💬 General Chat"
    
    @st.cache_resource
    def get_doc_processor(_self):
        """Get cached document processor instance."""
        try:
            return DocumentProcessor()
        except Exception as e:
            st.error(f"Failed to initialize document processor: {e}")
            return None
    
    @st.cache_resource
    def get_llm_handler(_self):
        """Get cached LLM handler instance."""
        try:
            return OfflineLLM()
        except Exception as e:
            st.error(f"Failed to initialize LLM handler: {e}")
            return None
    
    def render_header(self):
        """Render the main header."""
        st.markdown('<div class="main-header">🤖 Offline Chatbot</div>', unsafe_allow_html=True)
        st.markdown("**Choose your mode: 💬 General Chat (no documents needed) or 📄 Document Chat (upload documents first)**")
        st.markdown("---")
    
    def render_sidebar(self):
        """Render the sidebar with document management features."""
        with st.sidebar:
            st.title("🔧 System & Documents")
            
            # System status
            st.subheader("🤖 System Status")
            self.show_system_status()
            
            st.markdown("---")
            
            # Document upload
            st.subheader("📄 Upload Documents")
            st.caption("For Document Chat mode only")
            uploaded_files = st.file_uploader(
                "Choose files to process",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt'],
                help="Upload PDF, DOCX, or TXT files for document-based chat"
            )
            
            if uploaded_files:
                self.handle_file_upload(uploaded_files)
            
            st.markdown("---")
            
            # Database statistics
            st.subheader("📊 Database Stats")
            self.show_database_stats()
            
            st.markdown("---")
            
            # Management actions
            st.subheader("⚙️ Management")
            if st.button("🗑️ Clear All Documents", help="Remove all processed documents"):
                self.clear_documents()
    
    def show_system_status(self):
        """Display system status information."""
        if not self.llm_handler:
            st.error("❌ LLM Handler not initialized")
            return
        
        # Check LLM status
        model_status = self.llm_handler.check_model_availability()
        
        if model_status.get("available", False):
            st.success(f"✅ LLM Ready ({self.llm_handler.model})")
            st.info("💬 General Chat available!")
        else:
            st.error("❌ LLM Not Available")
            st.write("Please ensure Ollama is running and the model is installed.")
            
            if st.button("🔄 Test Connection"):
                test_result = self.llm_handler.test_connection()
                if test_result["success"]:
                    st.success("Connection successful!")
                    st.rerun()
                else:
                    st.error(f"Connection failed: {test_result['message']}")
                    if "suggestions" in test_result:
                        st.write("**Suggestions:**")
                        for suggestion in test_result["suggestions"]:
                            st.write(suggestion)
        
        # Document processor status
        if self.doc_processor:
            st.success("✅ Document Processor Ready")
            st.info("📄 Document Chat available!")
        else:
            st.error("❌ Document Processor Not Available")
    
    def handle_file_upload(self, uploaded_files):
        """Handle uploaded files and process them."""
        st.write(f"📁 {len(uploaded_files)} file(s) selected")
        
        # Show file details
        for file in uploaded_files:
            file_size_mb = len(file.read()) / (1024 * 1024)
            file.seek(0)  # Reset file pointer
            
            if file_size_mb > self.config.MAX_FILE_SIZE_MB:
                st.warning(f"⚠️ {file.name} is too large ({file_size_mb:.1f}MB > {self.config.MAX_FILE_SIZE_MB}MB)")
            else:
                st.write(f"✅ {file.name} ({file_size_mb:.1f}MB)")
        
        if st.button("🚀 Process Documents", type="primary"):
            self.process_uploaded_files(uploaded_files)
    
    def process_uploaded_files(self, uploaded_files):
        """Process uploaded files and create embeddings."""
        if not self.doc_processor:
            st.error("Document processor not available")
            return
        
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temporary directory
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())
                file_paths.append(file_path)
            
            # Process documents
            with st.spinner("Processing documents and creating embeddings..."):
                try:
                    results = self.doc_processor.process_documents(file_paths)
                    st.session_state.processing_status = results
                    st.session_state.documents_processed = True
                    
                    # Show results
                    if results["processed"] > 0:
                        st.success(f"✅ Successfully processed {results['processed']} document(s)")
                        st.info(f"📊 Created {results['total_chunks']} text chunks")
                        st.info("📄 You can now use Document Chat mode!")
                    
                    if results["failed"] > 0:
                        st.warning(f"⚠️ Failed to process {results['failed']} document(s)")
                        
                        if results["errors"]:
                            with st.expander("View Errors"):
                                for error in results["errors"]:
                                    st.write(f"• {error}")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing documents: {e}")
                    logger.error(f"Document processing error: {e}")
    
    def show_database_stats(self):
        """Display database statistics."""
        if not self.doc_processor:
            st.write("Database not available")
            return
        
        try:
            stats = self.doc_processor.get_collection_stats()
            
            if "error" in stats:
                st.error(f"Error: {stats['error']}")
            else:
                st.metric("Total Chunks", stats["total_chunks"])
                if stats["total_chunks"] > 0:
                    st.success("📄 Document Chat Ready!")
                else:
                    st.info("📄 No documents processed yet")
                
        except Exception as e:
            st.error(f"Error getting stats: {e}")
    
    def clear_documents(self):
        """Clear all documents from the database."""
        if not self.doc_processor:
            st.error("Document processor not available")
            return
        
        try:
            with st.spinner("Clearing all documents..."):
                self.doc_processor.clear_collection()
                st.session_state.documents_processed = False
                st.session_state.processing_status = {}
                st.success("✅ All documents cleared successfully")
                st.rerun()
        except Exception as e:
            st.error(f"Error clearing documents: {e}")
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        # Chat mode selection
        chat_mode = st.radio(
            "Choose chat mode:",
            ["💬 General Chat", "📄 Document Chat"],
            horizontal=True,
            help="General Chat: Direct conversation with AI. Document Chat: AI answers based on your uploaded documents.",
            key="chat_mode_selector"
        )
        
        # Update session state
        st.session_state.current_chat_mode = chat_mode
        
        # Mode-specific UI
        if chat_mode == "📄 Document Chat":
            st.subheader("📄 Chat with your Documents")
            if not st.session_state.documents_processed:
                st.info("💡 Upload and process documents first to enable document-based chat!")
                st.info("👈 Use the sidebar to upload files")
            else:
                st.success("✅ Document chat is ready! Ask questions about your documents.")
        else:
            st.subheader("💬 General Chat with AI")
            st.success("🤖 Ready for direct conversation with the AI model!")
        
        # Display chat history
        for message in st.session_state.chat_history:
            self.display_message(message)
        
        # Chat input with dynamic placeholder and state
        if chat_mode == "📄 Document Chat":
            placeholder = "Ask a question about your documents..." if st.session_state.documents_processed else "Upload documents first to enable document chat"
            disabled = not st.session_state.documents_processed
        else:
            placeholder = "Ask me anything..."
            disabled = False
        
        # Check if LLM is available
        if not self.llm_handler:
            st.error("❌ LLM not available. Please check Ollama installation.")
            disabled = True
        
        user_input = st.chat_input(placeholder, disabled=disabled)
        
        if user_input:
            self.handle_user_input(user_input, chat_mode)
    
    def display_message(self, message: Dict[str, Any]):
        """Display a chat message."""
        with st.chat_message(message["role"]):
            # Show mode indicator for user messages
            if message["role"] == "user" and "mode" in message:
                mode_icon = "📄" if message["mode"] == "📄 Document Chat" else "💬"
                st.markdown(f'<div class="mode-indicator">{mode_icon} {message["mode"]}</div>', unsafe_allow_html=True)
            
            st.write(message["content"])
            
            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                
                with st.expander("ℹ️ Response Details"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Mode:** {metadata.get('mode', 'Unknown')}")
                        st.write(f"**Context Used:** {metadata.get('context_used', 0)} chunks")
                        st.write(f"**Model:** {metadata.get('model', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**Response Tokens:** {metadata.get('response_tokens', 0)}")
                        st.write(f"**Processing Time:** {metadata.get('processing_time', 0):.2f}s")
                    
                    # Show source information if available (only for document mode)
                    if metadata.get("sources") and metadata.get('mode') == "📄 Document Chat":
                        st.write("**Sources:**")
                        for source in metadata["sources"]:
                            st.write(f"• {source}")
    
    def handle_user_input(self, user_input: str, chat_mode: str = "💬 General Chat"):
        """Handle user input and generate response."""
        if not self.llm_handler:
            st.error("LLM handler not available")
            return
        
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now(),
            "mode": chat_mode
        })
        
        # Generate response
        with st.spinner("Thinking..."):
            start_time = datetime.now()
            
            try:
                relevant_docs = []
                
                # Only search documents if in document chat mode AND documents are available
                if chat_mode == "📄 Document Chat" and self.doc_processor and st.session_state.documents_processed:
                    relevant_docs = self.doc_processor.search_similar_documents(
                        user_input, 
                        k=self.config.RETRIEVAL_K
                    )
                
                # Generate LLM response (with or without document context)
                context_docs = relevant_docs if chat_mode == "📄 Document Chat" else None
                llm_response = self.llm_handler.generate_response(user_input, context_docs=context_docs)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Prepare response metadata
                sources = []
                if relevant_docs and chat_mode == "📄 Document Chat":
                    sources = list(set([
                        doc.get("metadata", {}).get("source", "Unknown")
                        for doc in relevant_docs
                    ]))
                
                metadata = {
                    "context_used": len(relevant_docs) if chat_mode == "📄 Document Chat" else 0,
                    "model": llm_response.get("model", "Unknown"),
                    "response_tokens": llm_response.get("response_tokens", 0),
                    "processing_time": processing_time,
                    "sources": sources,
                    "success": llm_response.get("success", False),
                    "mode": chat_mode
                }
                
                # Add assistant response to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": llm_response["response"],
                    "timestamp": datetime.now(),
                    "metadata": metadata
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                logger.error(f"Response generation error: {e}")
    
    def run(self):
        """Run the main application."""
        self.render_header()
        self.render_sidebar()
        
        # Always show chat interface - it handles both modes
        self.render_chat_interface()

def main():
    """Main entry point for the application."""
    try:
        app = ChatbotApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
