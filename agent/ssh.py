"""
SSH Manager - Manage SSH connections to remote servers
"""
import os
import sys
import json
import time
import getpass
from typing import Optional, Dict, Any, List
import paramiko
from pathlib import Path


class SSHManager:
    """Manage SSH connections and execute commands on remote servers"""
    
    def __init__(self, config_path: str = "./servers.json", timeout: int = 60):
        self.config_path = config_path
        self.timeout = timeout  # Longer timeout for SSH
        self.servers = self._load_servers()
        self.clients: Dict[str, paramiko.SSHClient] = {}
    
    def _load_servers(self) -> List[Dict[str, str]]:
        """Load server configurations from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    return data.get("servers", [])
            except:
                pass
        return []
    
    def _save_servers(self) -> None:
        """Save server configurations to file"""
        with open(self.config_path, "w") as f:
            json.dump({"servers": self.servers}, f, indent=2)
    
    def add_server(
        self,
        name: str,
        host: str,
        user: str = "root",
        key_path: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        """Add a new server configuration"""
        server = {
            "name": name,
            "host": host,
            "user": user,
            "key_path": key_path,
            "password": password
        }
        self.servers.append(server)
        self._save_servers()
    
    def remove_server(self, name: str) -> bool:
        """Remove a server by name"""
        self.servers = [s for s in self.servers if s["name"] != name]
        self._save_servers()
        return True
    
    def list_servers(self) -> List[Dict[str, str]]:
        """List all configured servers"""
        return self.servers
    
    def connect(self, server_name: str, password_callback=None) -> bool:
        """Connect to a server with longer timeout and optional password callback"""
        server = self._get_server(server_name)
        if not server:
            return False
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect with longer timeout
            if server.get("key_path"):
                client.connect(
                    server["host"],
                    username=server["user"],
                    key_filename=server["key_path"],
                    timeout=self.timeout,
                    banner_timeout=self.timeout,
                    auth_timeout=self.timeout
                )
            elif server.get("password"):
                client.connect(
                    server["host"],
                    username=server["user"],
                    password=server["password"],
                    timeout=self.timeout,
                    banner_timeout=self.timeout,
                    auth_timeout=self.timeout
                )
            else:
                # Try to get password interactively
                password = None
                if password_callback:
                    password = password_callback(server_name)
                elif sys.stdin.isatty():  # Check if running in interactive mode
                    # For command line usage, prompt for password
                    password = getpass.getpass(f"Enter password for {server['user']}@{server['host']}: ")
                
                if password:
                    client.connect(
                        server["host"],
                        username=server["user"],
                        password=password,
                        timeout=self.timeout,
                        banner_timeout=self.timeout,
                        auth_timeout=self.timeout
                    )
                else:
                    client.connect(
                        server["host"],
                        username=server["user"],
                        timeout=self.timeout
                    )
            
            self.clients[server_name] = client
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def connect_with_password(
        self,
        host: str,
        user: str,
        password: str,
        timeout: int = 60
    ) -> paramiko.SSHClient:
        """Direct SSH connection with password (for one-off connections)"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                host,
                username=user,
                password=password,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout
            )
            return client
        except Exception as e:
            raise Exception(f"SSH connection failed: {e}")
    
    def disconnect(self, server_name: str) -> None:
        """Disconnect from a server"""
        if server_name in self.clients:
            self.clients[server_name].close()
            del self.clients[server_name]
    
    def run_command(
        self,
        server_name: str,
        command: str,
        timeout: int = 30,
        password_callback=None
    ) -> Dict[str, Any]:
        """Run a command on a remote server"""
        # Connect if not connected
        if server_name not in self.clients:
            if not self.connect(server_name, password_callback):
                return {"error": "Failed to connect"}
        
        client = self.clients[server_name]
        
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            
            return {
                "stdout": stdout_data,
                "stderr": stderr_data,
                "exit_code": exit_code
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_command_direct(
        self,
        host: str,
        user: str,
        command: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Run a command directly without saving server config"""
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if key_path:
                client.connect(
                    host,
                    username=user,
                    key_filename=key_path,
                    timeout=timeout,
                    banner_timeout=timeout,
                    auth_timeout=timeout
                )
            elif password:
                client.connect(
                    host,
                    username=user,
                    password=password,
                    timeout=timeout,
                    banner_timeout=timeout,
                    auth_timeout=timeout
                )
            else:
                client.connect(host, username=user, timeout=timeout)
            
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            
            return {
                "stdout": stdout_data,
                "stderr": stderr_data,
                "exit_code": exit_code
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            if client:
                client.close()
    
    def _get_server(self, name: str) -> Optional[Dict[str, str]]:
        """Get server config by name"""
        for s in self.servers:
            if s["name"] == name:
                return s
        return None
    
    def __del__(self):
        """Clean up connections"""
        for client in self.clients.values():
            client.close()


# Safety: Block dangerous commands
BLOCKED_COMMANDS = [
    "rm -rf /",
    "shutdown",
    "reboot",
    ":(){:|:&};:",
    "mkfs",
    "dd if=/dev/zero"
]


def safe_run(command: str) -> str:
    """Check and run command safely"""
    for blocked in BLOCKED_COMMANDS:
        if blocked in command.lower():
            return f"BLOCKED: Dangerous command detected: {blocked}"
    return None  # Safe to run


# Convenience functions
def create_ssh_manager(config_path: str = "./servers.json", timeout: int = 60) -> SSHManager:
    """Create an SSH manager instance"""
    return SSHManager(config_path, timeout)


def ssh_run_command(
    host: str,
    user: str,
    command: str,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """Quick SSH command execution (for agent tool use)"""
    manager = SSHManager(timeout=timeout)
    return manager.run_command_direct(host, user, command, password, key_path, timeout)