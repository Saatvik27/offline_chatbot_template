# Offline Chatbot Template

A secure, offline chatbot that provides two powerful modes: **General Chat** for direct AI conversation and **Document Chat** for analyzing your uploaded documents.

## 🌟 Two Chat Modes

### 💬 **General Chat Mode**
- Direct conversation with AI - no documents needed
- Perfect for general questions, brainstorming, coding help
- Works immediately after setup

### 📄 **Document Chat Mode** 
- AI analyzes and answers questions about your uploaded documents
- Supports PDF, DOCX, and TXT files
- Perfect for research, document analysis, and Q&A

## ✨ Features

- 🔒 **Complete Offline Operation** - No data leaves your machine
- 🤖 **Dual Chat Modes** - General conversation + document analysis
- 📄 **Multi-format Support** - PDF, DOCX, and TXT files
- 🧠 **Vector Embeddings** - Intelligent document search
- 🎯 **Local LLM** - Uses Ollama for offline AI responses
- 🖥️ **Modern UI** - Clean, intuitive Streamlit interface

## Step-by-Step Setup

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Ollama
- Download from: https://ollama.ai/
- Install a model: `ollama pull llama2`

### Step 3: Run the Application
```bash
streamlit run app.py
```

## Usage

1. Upload documents using the sidebar
2. Process documents to create embeddings
3. Ask questions about your documents
4. Get AI-powered contextual answers

## Security

- All processing happens locally
- No data sent to external servers
- Documents stored locally only
