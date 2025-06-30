# Offline Chatbot Template - Quick Start

Transform this into a fast, deployable backend API that works with any frontend!

## 🚀 Quick Setup (Backend API)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install & Setup Ollama
**Windows:**
- Download from: https://ollama.ai/download/windows  
- Install and restart your terminal
- Download a model: `ollama pull llama3.1:8b`

**Linux/macOS:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama3.1:8b
```

### Step 3: Start the API Server
```bash
# Option 1: Direct Python
python api_server.py

# Option 2: Using uvicorn (recommended)
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

**API will be available at: http://localhost:8000**

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API status |
| `/chat` | POST | Send chat messages |
| `/upload-documents` | POST | Upload documents |
| `/documents/stats` | GET | Get document statistics |
| `/docs` | GET | Interactive API documentation |

## 📱 Frontend Integration

### Quick Test (HTML)
Open `frontend_example.html` in your browser for a ready-to-use chat interface.

### JavaScript Example
```javascript
// Send a chat message
const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "Hello!",
        mode: "general"  // or "document"
    })
});

const data = await response.json();
console.log(data.response); // AI response
```

### React Example
```jsx
const sendMessage = async (message) => {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, mode: 'general' })
    });
    return await response.json();
};
```

## 🚀 Deployment Options

### Option 1: Auto-Deploy Script
```bash
python deploy.py --docker --systemd --nginx
```

### Option 2: Docker (Recommended)
```bash
# Build and run
docker-compose up -d

# API available at http://localhost:8000
```

### Option 3: Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## ⚡ Performance Optimizations Applied

1. **Reduced Response Time**: 
   - Shorter prompts for general chat
   - Limited context chunks (top 3)
   - Reduced token limits (256 tokens)
   - Async processing with thread pools

2. **Fast API**: 
   - FastAPI instead of Streamlit
   - Non-blocking operations
   - Concurrent request handling

3. **Optimized Model Settings**:
   - Reduced timeout (30s → faster failure)
   - Better Ollama parameters
   - Streamlined prompt templates

## 🔧 Configuration

Copy `.env.example` to `.env` and modify:
```bash
API_HOST=0.0.0.0
API_PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
```

## 🎯 Two Chat Modes

### 💬 **General Chat**
- Instant responses
- No document upload needed
- Perfect for general AI assistance

### 📄 **Document Chat**
1. Upload documents via `/upload-documents` endpoint
2. Use mode: "document" in chat requests
3. AI answers based on uploaded content

## 📊 Monitoring

- **Health Check**: `GET /health`
- **API Docs**: `http://localhost:8000/docs`
- **Metrics**: Response times included in chat responses

## 🐛 Troubleshooting

**Slow responses?**
- Check if Ollama is using GPU: `ollama ps`
- Reduce model size: `ollama pull llama3.1:latest` → `llama3.1:8b`

**Connection errors?**
- Verify Ollama is running: `ollama serve`
- Check port 11434 is accessible
- Test with: `curl http://localhost:11434/api/tags`

**Model not found?**
```bash
ollama list  # See available models
ollama pull llama3.1:8b  # Download if missing
```

---

**🎉 Ready to integrate with any frontend framework: React, Angular, Vue, Flutter, or mobile apps!**
