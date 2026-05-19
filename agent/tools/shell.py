"""
Shell Tool - Execute shell commands on the server
"""
import subprocess
from typing import Optional, Any
from langchain_core.tools import BaseTool


class ShellTool(BaseTool):
    """Tool for executing shell commands on the server"""
    
    name: str = "shell"
    description: str = """Execute shell commands on the server. Use this for:
    - Running system commands (ls, cat, grep, etc.)
    - Managing services (systemctl, docker, etc.)
    - Checking system status and logs
    - File operations not covered by other tools
    
    Input should be a valid shell command string."""
    
    def _run(self, command: str, timeout: Optional[int] = None) -> str:
        """Execute a shell command and return the output"""
        from ..config import get_config
        config = get_config()
        timeout = timeout or config.shell_timeout
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            return "\n".join(output) if output else "Command executed successfully with no output."
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"


# Convenience function for direct use
def run_shell(command: str, timeout: Optional[int] = None) -> str:
    """Execute a shell command directly"""
    tool = ShellTool()
    return tool._run(command, timeout)