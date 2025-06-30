#!/usr/bin/env python3
"""
Deployment script for the Offline Chatbot API
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✅ Python {sys.version} detected")

def install_requirements():
    """Install required packages."""
    print("📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def check_ollama():
    """Check if Ollama is installed and running."""
    print("🤖 Checking Ollama...")
    try:
        # Check if ollama command exists
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        print("✅ Ollama is installed")
        
        # Check if service is running
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama service is running")
            models = result.stdout.strip()
            if models:
                print(f"📋 Available models:\n{models}")
            else:
                print("⚠️  No models found. You may need to pull a model:")
                print("   ollama pull llama3.1:8b")
        else:
            print("⚠️  Ollama service may not be running. Try: ollama serve")
            
    except subprocess.CalledProcessError:
        print("❌ Ollama not found. Please install from https://ollama.ai/")
        print("After installation, run: ollama pull llama3.1:8b")

def create_docker_files():
    """Create Docker configuration files."""
    print("🐳 Creating Docker configuration...")
    
    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p chroma_db uploaded_docs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    # docker-compose.yml
    compose_content = """version: '3.8'

services:
  chatbot-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./uploaded_docs:/app/uploaded_docs
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  default:
    driver: bridge
"""
    
    # .dockerignore
    dockerignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
.env
.git/
.gitignore
README.md
*.md
.DS_Store
Thumbs.db
node_modules/
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    with open(".dockerignore", "w") as f:
        f.write(dockerignore_content)
    
    print("✅ Docker files created successfully")

def create_env_file():
    """Create environment configuration file."""
    env_content = """# Offline Chatbot Configuration

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b

# Database Settings
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=document_embeddings

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=10
RETRIEVAL_K=5

# Security (configure for production)
ALLOWED_ORIGINS=["*"]
"""
    
    with open(".env.example", "w") as f:
        f.write(env_content)
    
    print("✅ Environment configuration created (.env.example)")

def create_systemd_service():
    """Create systemd service file for Linux deployment."""
    if os.name != 'posix':
        return
    
    service_content = f"""[Unit]
Description=Offline Chatbot API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/.venv/bin
ExecStart={os.getcwd()}/.venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("chatbot-api.service", "w") as f:
        f.write(service_content)
    
    print("✅ Systemd service file created (chatbot-api.service)")
    print("📋 To install on Linux:")
    print("   sudo cp chatbot-api.service /etc/systemd/system/")
    print("   sudo systemctl enable chatbot-api")
    print("   sudo systemctl start chatbot-api")

def create_nginx_config():
    """Create nginx configuration for production deployment."""
    nginx_content = """server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Increase max file upload size for documents
    client_max_body_size 50M;
}
"""
    
    with open("nginx-chatbot-api.conf", "w") as f:
        f.write(nginx_content)
    
    print("✅ Nginx configuration created (nginx-chatbot-api.conf)")

def main():
    parser = argparse.ArgumentParser(description="Deploy Offline Chatbot API")
    parser.add_argument("--docker", action="store_true", help="Create Docker configuration")
    parser.add_argument("--systemd", action="store_true", help="Create systemd service")
    parser.add_argument("--nginx", action="store_true", help="Create nginx configuration")
    parser.add_argument("--skip-install", action="store_true", help="Skip installing requirements")
    
    args = parser.parse_args()
    
    print("🚀 Offline Chatbot API Deployment Setup")
    print("=" * 40)
    
    check_python_version()
    
    if not args.skip_install:
        install_requirements()
    
    check_ollama()
    create_env_file()
    
    if args.docker:
        create_docker_files()
    
    if args.systemd:
        create_systemd_service()
    
    if args.nginx:
        create_nginx_config()
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Configure your environment variables (copy .env.example to .env)")
    print("2. Ensure Ollama is running: ollama serve")
    print("3. Pull the required model: ollama pull llama3.1:8b")
    print("4. Start the API server:")
    print("   python api_server.py")
    print("   OR")
    print("   uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload")
    print("\n🌐 API will be available at:")
    print("   - Health check: http://localhost:8000/health")
    print("   - Documentation: http://localhost:8000/docs")
    print("   - Chat endpoint: http://localhost:8000/chat")

if __name__ == "__main__":
    main()
