#!/usr/bin/env python3
"""
Test script to verify password prompting functionality
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agent.ssh import SSHManager

def test_ssh_password_prompt():
    """Test SSH connection with password prompt"""
    print("Testing SSH password prompt functionality...")
    
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
    
    # Test connection
    server_name = servers[0]['name']  # Test with first server
    print(f"\nTesting connection to {server_name}...")
    
    try:
        if ssh_manager.connect(server_name):
            print("✅ Connection successful!")
            
            # Test command
            result = ssh_manager.run_command(server_name, "whoami")
            if 'stdout' in result:
                print(f"✅ Command successful! User: {result['stdout'].strip()}")
            else:
                print(f"❌ Command failed: {result.get('error', 'Unknown error')}")
            
            # Disconnect
            ssh_manager.disconnect(server_name)
            print("✅ Disconnected")
        else:
            print("❌ Connection failed")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ssh_password_prompt()
