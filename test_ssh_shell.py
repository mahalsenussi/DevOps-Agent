#!/usr/bin/env python3
"""
Test script to verify SSH shell functionality
"""
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agent.ssh import SSHManager

def test_ssh_shell():
    """Test SSH shell session functionality"""
    print("Testing SSH shell functionality...")
    
    # Create SSH manager
    ssh_manager = SSHManager("./servers.json")
    
    # List available servers
    servers = ssh_manager.list_servers()
    if not servers:
        print("No servers configured. Please add a server to servers.json")
        return
    
    print("Available servers:")
    for server in servers:
        print(f"  - {server['name']}: {server['user']}@{server['host']}")
    
    # Test connection and shell
    server_name = servers[0]['name']  # Test with first server
    print(f"\nTesting shell connection to {server_name}...")
    
    try:
        if ssh_manager.connect(server_name):
            print("✅ Connection successful!")
            
            # Start shell
            client = ssh_manager.clients[server_name]
            shell = client.invoke_shell()
            print("✅ Shell started!")
            
            # Send some test commands
            commands = ['whoami\n', 'pwd\n', 'ls -la\n', 'exit\n']
            
            for cmd in commands:
                print(f"Sending: {cmd.strip()}")
                shell.send(cmd.encode())
                time.sleep(1)  # Wait for response
                
                # Read output
                while shell.recv_ready():
                    output = shell.recv(1024).decode()
                    print(f"Output: {output.strip()}")
                
                time.sleep(0.5)
            
            # Close shell and disconnect
            shell.close()
            ssh_manager.disconnect(server_name)
            print("✅ Shell test completed!")
            
        else:
            print("❌ Connection failed")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ssh_shell()
