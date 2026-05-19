"""
DevOps Agent - Autonomous server management agent powered by Ollama + LangGraph
"""

__version__ = "1.0.0"

from .agent import get_agent, DevOpsAgent
from .autonomous import run_autonomous, AutonomousAgent
from .config import get_config, update_config
from .tools import ShellTool, WebSearchTool, FileSystemTool, run_shell, web_search
from .ssh import SSHManager
from .memory import get_memory

__all__ = [
    "get_agent",
    "DevOpsAgent",
    "run_autonomous",
    "AutonomousAgent",
    "get_config",
    "update_config",
    "ShellTool",
    "WebSearchTool",
    "FileSystemTool",
    "run_shell",
    "web_search",
    "SSHManager",
    "get_memory"
]