"""
LLM Client - Ollama integration for the agent
"""
from typing import Optional, Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .config import get_config


class OllamaClient:
    """Ollama LLM client wrapper with chat interface"""
    
    def __init__(self, model: Optional[str] = None, temperature: Optional[float] = None):
        config = get_config()
        self.model = model or config.ollama_model
        self.temperature = temperature or config.temperature
        self.base_url = config.ollama_base_url
        
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature
        )
        
    def invoke(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Simple invoke with optional system prompt"""
        if system_prompt:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            return self.llm.invoke(messages)
        return self.llm.invoke(prompt)
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with messages in OpenAI format"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
                
        return self.llm.invoke(langchain_messages)
    
    def __repr__(self) -> str:
        return f"OllamaClient(model={self.model}, temperature={self.temperature})"


def get_llm() -> OllamaClient:
    """Get default LLM client instance"""
    return OllamaClient()