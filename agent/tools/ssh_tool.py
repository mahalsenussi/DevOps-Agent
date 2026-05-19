"""
SSH Tool - Direct SSH connection for the agent

This tool allows the agent to connect to remote servers
using either password or key authentication.
"""
import json
from typing import Optional
from langchain_core.tools import BaseTool


class SSHTool(BaseTool):
    """Tool for SSH connections to remote servers"""
    
    name: str = "ssh"
    description: str = """Execute commands on remote servers via SSH.
    
    Input format (JSON):
    {"host": "10.147.18.5", "user": "mahmoud", "password": "loraly", "command": "uptime"}
    OR with key:
    {"host": "10.147.18.5", "user": "mahmoud", "key_path": "~/.ssh/key", "command": "uptime"}
    
    Use this for:
    - Connecting to remote servers
    - Running commands on remote systems
    - Checking server status
    - Managing services on remote hosts"""
    
    def _run(self, args: str) -> str:
        """Execute SSH command"""
        from ..ssh import ssh_run_command
        
        # Parse the input
        try:
            if "{" in args:
                start = args.find("{")
                end = args.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = args[start:end]
                    params = json.loads(json_str)
                else:
                    return f"Error: Invalid input format. Use JSON: {self.description}"
            else:
                return f"Error: Invalid input. Use JSON format: {self.description}"
            
            host = params.get("host", "")
            user = params.get("user", "root")
            command = params.get("command", "")
            password = params.get("password")
            key_path = params.get("key_path")
            timeout = params.get("timeout", 60)  # Default 60 second timeout
            
            if not host or not command:
                return "Error: host and command are required"
            
            # Run SSH command
            result = ssh_run_command(
                host=host,
                user=user,
                command=command,
                password=password,
                key_path=key_path,
                timeout=timeout
            )
            
            if "error" in result:
                return f"SSH Error: {result['error']}"
            
            output = []
            if result.get("stdout"):
                output.append(result["stdout"])
            if result.get("stderr"):
                output.append(f"STDERR: {result['stderr']}")
            output.append(f"Exit code: {result.get('exit_code', 0)}")
            
            return "\n".join(output)
            
        except json.JSONDecodeError as e:
            err_msg = "Error parsing JSON: " + str(e) + "\n\nUse format: {\"host\": \"ip\", \"user\": \"name\", \"password\": \"pass\", \"command\": \"cmd\"}"
            return err_msg
        except Exception as e:
            return f"Error: {str(e)}"


# Convenience function
def run_ssh(
    host: str,
    user: str,
    command: str,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
    timeout: int = 60
) -> str:
    """Run SSH command directly"""
    tool = SSHTool()
    params = {
        "host": host,
        "user": user,
        "command": command,
        "timeout": timeout
    }
    if password:
        params["password"] = password
    if key_path:
        params["key_path"] = key_path
    
    return tool._run(json.dumps(params))