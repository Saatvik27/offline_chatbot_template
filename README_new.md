# Offline Chatbot Template

A fast, deployable backend API for offline document-based and general chat that can integrate with any frontend framework.

## 🚀 Features

- **Fast API Backend**: Built with FastAPI for high performance
- **Dual Chat Modes**: General conversation + Document-based Q&A
- **Frontend Agnostic**: Works with React, Angular, Vue, Flutter, mobile apps
- **Offline First**: Runs completely offline using Ollama
- **Optimized Performance**: Sub-5-second response times
- **Easy Deployment**: Docker, systemd, and cloud-ready
- **Document Processing**: PDF, DOCX, TXT support with vector search

## 📁 Project Structure

```
├── api_server.py           # FastAPI backend server
├── app.py                  # Original Streamlit UI (optional)
├── llm_handler.py          # Optimized LLM interface
├── document_processor.py   # Document processing & vector DB
├── config.py              # Configuration settings
├── deploy.py              # Automated deployment script
├── frontend_example.html   # Example frontend integration
├── requirements.txt       # Python dependencies
├── QUICKSTART.md          # Quick setup guide
└── README.md              # This file
```

## ⚡ Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Ollama**:
   ```bash
   # Install Ollama (https://ollama.ai)
   ollama pull llama3.1:8b
   ```

3. **Start the API**:
   ```bash
   python api_server.py
   # API available at http://localhost:8000
   ```

4. **Test with example frontend**:
   Open `frontend_example.html` in your browser

## 🌐 API Integration

### Chat Endpoint
```javascript
POST /chat
{
    "message": "Hello!",
    "mode": "general"  // or "document"
}

Response:
{
    "response": "Hello! How can I help you?",
    "mode": "general",
    "processing_time": 1.2,
    "conversation_id": "conv_123",
    "metadata": {...}
}
```

### Document Upload
```javascript
POST /upload-documents
Content-Type: multipart/form-data

// FormData with files
```

### Health Check
```javascript
GET /health
{
    "status": "healthy",
    "ollama_available": true,
    "document_processor_available": true,
    "total_documents": 5
}
```

## 🎯 Frontend Examples

### Vanilla JavaScript
```javascript
const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "Explain quantum computing",
        mode: "general"
    })
});
const data = await response.json();
console.log(data.response);
```

### React Hook
```jsx
import { useState } from 'react';

function useChat() {
    const [loading, setLoading] = useState(false);
    
    const sendMessage = async (message, mode = 'general') => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, mode })
            });
            return await response.json();
        } finally {
            setLoading(false);
        }
    };
    
    return { sendMessage, loading };
}
```

### Flutter/Dart
```dart
Future<Map<String, dynamic>> sendMessage(String message, String mode) async {
    final response = await http.post(
        Uri.parse('http://localhost:8000/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message, 'mode': mode}),
    );
    return jsonDecode(response.body);
}
```

## 🚀 Deployment

### Auto-Deploy Script
```bash
python deploy.py --docker --systemd --nginx
```

### Docker (Recommended)
```bash
docker-compose up -d
```

### Production with Nginx
```bash
# Start API
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000

# Configure nginx (example config provided)
sudo cp nginx-chatbot-api.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/chatbot-api /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## ⚡ Performance Features

- **Async Processing**: Non-blocking operations with thread pools
- **Optimized Prompts**: Reduced token usage for faster responses
- **Smart Caching**: Efficient model loading and reuse
- **Concurrent Handling**: Multiple requests processed simultaneously
- **Timeout Management**: Quick failure detection and recovery

## 📊 Monitoring & Health

- **Real-time Status**: `/health` endpoint for monitoring
- **Response Metrics**: Processing time included in responses
- **Error Handling**: Comprehensive error responses with details
- **Logging**: Structured logging for debugging and monitoring

## 🔧 Configuration

Environment variables (`.env`):
```bash
API_HOST=0.0.0.0
API_PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
CHUNK_SIZE=1000
RETRIEVAL_K=5
```

## 🛠️ Development

### Run in Development Mode
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

### Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "mode": "general"}'
```

## 🔍 Troubleshooting

**Slow Response Times:**
- Ensure Ollama is using GPU acceleration
- Use smaller models (7B instead of 13B+)
- Reduce `num_predict` in config
- Check system resources

**Connection Issues:**
- Verify Ollama is running: `ollama serve`
- Check port 11434 accessibility
- Ensure model is downloaded: `ollama pull llama3.1:8b`

**Memory Issues:**
- Use smaller embedding models
- Reduce chunk size in document processing
- Limit concurrent requests

## 📱 Mobile App Integration

This API works perfectly with mobile frameworks:

- **React Native**: Use fetch() as shown above
- **Flutter**: Use http package as shown above  
- **iOS/Swift**: Use URLSession with JSON requests
- **Android/Kotlin**: Use Retrofit or OkHttp

## 🌟 Use Cases

- **Customer Support Bots**: Upload manuals, provide instant answers
- **Knowledge Base Chat**: Internal company documents Q&A
- **Educational Tools**: Subject-specific tutoring systems
- **Code Documentation**: Developer assistance with codebases
- **Personal Assistant**: General conversation + document management

## 📄 License

MIT License - feel free to use in commercial projects!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Transform your ideas into production-ready chat applications with this fast, scalable template!** 🚀
