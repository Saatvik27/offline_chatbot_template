import logging
import requests
import json
from typing import List, Dict, Any, Optional
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineLLM:
    """Handles communication with local LLM via Ollama."""
    
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.get_ollama_url()
        self.model = self.config.LLM_MODEL
        self._check_ollama_connection()
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"].split(":")[0] for model in models]
                
                if self.model not in model_names:
                    logger.warning(f"Model '{self.model}' not found. Available models: {model_names}")
                    return False
                
                logger.info(f"Ollama connection successful. Model '{self.model}' available.")
                return True
            else:
                logger.error(f"Ollama not accessible. Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def generate_response(self, prompt: str, context_docs: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate response using local LLM with optional context."""
        try:
            # Build the enhanced prompt with context
            enhanced_prompt = self._build_context_prompt(prompt, context_docs)
            
            # Debug logging
            logger.info(f"Context docs provided: {context_docs is not None}")
            logger.info(f"Number of context docs: {len(context_docs) if context_docs else 0}")
            if not context_docs:
                logger.info("Using GENERAL CHAT mode - no documents")
            
            # Prepare request payload with optimized settings for speed
            payload = {
                "model": self.model,
                "prompt": enhanced_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 256,  # Reduced for faster responses
                    "num_ctx": 2048,     # Context window
                    "stop": ["User:", "Human:"],
                    "repeat_penalty": 1.1,
                    "seed": -1,
                    "tfs_z": 1.0,
                    "num_keep": 0,
                    "typical_p": 1.0,
                    "presence_penalty": 0.0,
                    "frequency_penalty": 0.0,
                    "mirostat": 0,
                    "mirostat_tau": 5.0,
                    "mirostat_eta": 0.1,
                    "penalize_newline": True,
                    "numa": False
                }
            }
            
            # Make request to Ollama with reduced timeout for faster responses
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30  # Reduced from 60 seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", "").strip(),
                    "model": self.model,
                    "context_used": len(context_docs) if context_docs else 0,
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "response_tokens": result.get("eval_count", 0)
                }
            else:
                logger.error(f"LLM request failed. Status: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response": "Sorry, I encountered an error while generating a response."
                }
                
        except requests.exceptions.Timeout:
            logger.error("LLM request timed out")
            return {
                "success": False,
                "error": "Request timed out",
                "response": "Sorry, the request took too long to process. Please try again."
            }
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an unexpected error. Please try again."
            }
    
    def _build_context_prompt(self, user_query: str, context_docs: Optional[List[Dict]] = None) -> str:
        """Build an enhanced prompt with relevant document context."""
        
        if not context_docs:
            # General Chat Mode - Simple and fast prompt
            return f"You are a helpful AI assistant. Answer concisely.\n\nUser: {user_query}\nAssistant:"
        else:
            # Document Chat Mode - Context provided
            system_prompt = "You are an AI assistant that answers questions based on provided documents. Be concise and reference the documents when relevant."
            
            # Build context from retrieved documents (limit for speed)
            context_text = "\n\nRelevant information:\n"
            for i, doc in enumerate(context_docs[:3], 1):  # Limit to top 3 for speed
                content = doc.get("content", "")[:500]  # Truncate for speed
                context_text += f"{i}. {content}\n"
            
            return f"{system_prompt}\n{context_text}\nUser Question: {user_query}\nAssistant:"
    
    def check_model_availability(self) -> Dict[str, Any]:
        """Check available models and current model status."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                available_models = [model["name"] for model in models_data]
                
                return {
                    "available": True,
                    "current_model": self.model,
                    "available_models": available_models,
                    "model_loaded": self.model in [m.split(":")[0] for m in available_models]
                }
            else:
                return {
                    "available": False,
                    "error": f"HTTP {response.status_code}",
                    "current_model": self.model
                }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "current_model": self.model
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the current model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and basic functionality."""
        try:
            # Test basic connection
            connection_status = self._check_ollama_connection()
            
            if not connection_status:
                return {
                    "success": False,
                    "message": "Cannot connect to Ollama. Please ensure Ollama is running.",
                    "suggestions": [
                        "1. Install Ollama from https://ollama.ai/",
                        f"2. Run 'ollama pull {self.model}' to download the model",
                        "3. Ensure Ollama is running on the default port (11434)"
                    ]
                }
            
            # Test model response with a simple query
            test_response = self.generate_response("Hello")
            
            return {
                "success": test_response["success"],
                "message": "Connection successful!" if test_response["success"] else "Connection failed",
                "model_response": test_response.get("response", ""),
                "error": test_response.get("error")
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": str(e)
            }
