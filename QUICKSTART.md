# Quick Start Guide

Get your offline chatbot running in 3 simple steps.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Install Ollama

**Windows:**
- Download from: https://ollama.ai/download/windows
- Install and restart your terminal
- Download a model: `ollama pull llama2`

**Linux/macOS:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2
```

## Step 3: Start the Application

```bash
streamlit run app.py
```

# Quick Start Guide

Get your offline chatbot running in 3 simple steps.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Install Ollama

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

## Step 3: Start the Application

```bash
streamlit run app.py
```

## 🎯 Two Ways to Use

### 💬 **General Chat (Immediate)**
- Select "General Chat" mode
- Start chatting right away - no documents needed!
- Perfect for questions, brainstorming, or general AI assistance

### 📄 **Document Chat (Upload First)**
1. Upload documents via sidebar (PDF, DOCX, TXT)
2. Click "Process Documents" 
3. Select "Document Chat" mode
4. Ask questions about your documents

## Example Questions

**General Chat:**
- "Explain machine learning concepts"
- "Help me debug this code"
- "Write a professional email"

**Document Chat:**
- "What are the main features in this document?"
- "Summarize the key points"
- "What are the system requirements?"

---

**Having issues?** Check the console for error messages or verify Ollama is running with `ollama --version`
