#!/usr/bin/env python3
"""
Custom Model Training Helper for Offline Chatbot
Creates a fine-tuned model using Ollama Modelfile approach
"""

import os
import json
from typing import List, Dict

class ModelTrainer:
    """Helper class for creating custom models with Ollama."""
    
    def __init__(self, base_model: str = "llama3.1:8b"):
        self.base_model = base_model
        self.training_data = []
    
    def add_training_example(self, instruction: str, response: str):
        """Add a training example."""
        self.training_data.append({
            "instruction": instruction,
            "response": response
        })
    
    def load_training_data(self, file_path: str):
        """Load training data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                self.add_training_example(
                    item.get("instruction", ""),
                    item.get("response", "")
                )
    
    def create_modelfile(self, custom_model_name: str, system_prompt: str = None):
        """Create a Modelfile for the custom model."""
        
        if system_prompt is None:
            system_prompt = f"""You are a helpful AI assistant trained on custom data. 
Provide accurate, helpful responses based on your training. 
If you're unsure about something, say so honestly."""
        
        modelfile_content = f"""FROM {self.base_model}

# Custom parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "### Instruction:"

# Custom template
TEMPLATE \"\"\"### Instruction:
{{{{ .Prompt }}}}

### Response:
\"\"\"

# System message
SYSTEM \"\"\"{system_prompt}\"\"\"

# Training examples (few-shot learning)
"""
        
        # Add training examples as few-shot prompts
        for i, example in enumerate(self.training_data[:5]):  # Use first 5 as examples
            modelfile_content += f"""
MESSAGE user "{example['instruction']}"
MESSAGE assistant "{example['response']}"
"""
        
        # Save Modelfile
        with open(f"Modelfile-{custom_model_name}", 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        print(f"✅ Modelfile created: Modelfile-{custom_model_name}")
        print(f"📋 Next steps:")
        print(f"   1. ollama create {custom_model_name} -f Modelfile-{custom_model_name}")
        print(f"   2. ollama run {custom_model_name} 'test question'")
        print(f"   3. Update your config.py: LLM_MODEL = '{custom_model_name}'")
        
        return f"Modelfile-{custom_model_name}"

# Example usage
if __name__ == "__main__":
    trainer = ModelTrainer()
    
    # Add some example training data
    trainer.add_training_example(
        "What is the company remote work policy?",
        "Our company supports flexible remote work. Employees can work from home full-time or hybrid, with weekly team check-ins required."
    )
    
    trainer.add_training_example(
        "How do I submit vacation requests?",
        "Vacation requests should be submitted via the HR portal at least 2 weeks in advance. Manager approval is required for requests over 5 days."
    )
    
    trainer.add_training_example(
        "What are our security protocols?",
        "All employees must use VPN for remote access, enable 2FA on company accounts, and follow the clean desk policy in office."
    )
    
    # Create the model
    trainer.create_modelfile(
        "company-assistant",
        "You are a helpful company assistant with knowledge of internal policies and procedures."
    )
