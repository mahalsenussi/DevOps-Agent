"""
Agent Configuration - Central configuration for the DevOps Agent
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for the DevOps Agent"""
    
    # Ollama settings
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3-vl:235b-cloud")
    
    # Agent behavior
    max_iterations: int = 10
    max_tool_calls: int = 5
    temperature: float = 0.7
    
    # Memory settings
    memory_enabled: bool = True
    memory_persist_dir: str = "./data/memory"
    
    # Tool settings
    shell_timeout: int = 30
    web_search_max_results: int = 5
    
    # MCP settings
    mcp_server_enabled: bool = False
    mcp_server_port: int = 8000


# Global config instance
config = AgentConfig()


def get_config() -> AgentConfig:
    """Get the global configuration instance"""
    return config


def update_config(**kwargs) -> None:
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)