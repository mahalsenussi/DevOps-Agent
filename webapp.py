"""
Flask Web Interface for DevOps Agent

Features:
- Terminal emulator for shell commands
- Agent task interface
- SSH server management
- Memory search
"""
import os
import sys
import subprocess
import json
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agent import get_agent, run_autonomous, SSHManager, get_memory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devops-agent-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global SSH manager
ssh_manager = SSHManager("./servers.json")

# Active SSH connections
ssh_connections = {}
ssh_shells = {}  # Store interactive shell sessions


@app.route('/')
def index():
    return render_template('index.html')


# === Shell Terminal Endpoints ===
@socketio.on('shell_command')
def handle_shell_command(data):
    """Execute shell command and stream output"""
    command = data.get('command', '')
    
    # Send command echo
    emit('shell_output', {'type': 'command', 'data': f'$ {command}'})
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                emit('shell_output', {'type': 'output', 'data': line})
        
        process.wait()
        emit('shell_output', {'type': 'done', 'data': f'Exit code: {process.returncode}'})
        
    except Exception as e:
        emit('shell_output', {'type': 'error', 'data': str(e)})


# === Smart Command Handler (Manual + AI) ===
@socketio.on('smart_command')
def handle_smart_command(data):
    """
    Handle both manual commands and AI tasks:
    - Commands starting with '!' = shell command
    - Commands starting with 'ssh:' = SSH command  
    - Everything else = AI agent task
    """
    command = data.get('command', '').strip()
    
    if not command:
        return
    
    # Detect command type
    if command.startswith('!'):
        # Shell command
        shell_cmd = command[1:].strip()
        emit('smart_output', {'type': 'command', 'data': f'$ {shell_cmd}', 'mode': 'shell'})
        
        try:
            process = subprocess.Popen(
                shell_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    emit('smart_output', {'type': 'output', 'data': line, 'mode': 'shell'})
            
            process.wait()
            emit('smart_output', {'type': 'done', 'data': f'Exit code: {process.returncode}', 'mode': 'shell'})
            
        except Exception as e:
            emit('smart_output', {'type': 'error', 'data': str(e), 'mode': 'shell'})
            
    elif command.startswith('ssh:'):
        # SSH command: ssh:server:command
        parts = command[4:].split(':', 2)
        if len(parts) >= 3:
            server = parts[0]
            ssh_cmd = parts[2]
            
            emit('smart_output', {'type': 'command', 'data': f'ssh {server}$ {ssh_cmd}', 'mode': 'ssh'})
            
            try:
                result = ssh_manager.run_command(server, ssh_cmd)
                if result.get('stdout'):
                    emit('smart_output', {'type': 'output', 'data': result['stdout'], 'mode': 'ssh'})
                if result.get('stderr'):
                    emit('smart_output', {'type': 'error', 'data': result['stderr'], 'mode': 'ssh'})
                emit('smart_output', {'type': 'done', 'data': f'Exit code: {result.get("exit_code", 0)}', 'mode': 'ssh'})
            except Exception as e:
                emit('smart_output', {'type': 'error', 'data': str(e), 'mode': 'ssh'})
        else:
            emit('smart_output', {'type': 'error', 'data': 'Usage: ssh:server:command', 'mode': 'ssh'})
            
    else:
        # AI Agent task - run with progress callback
        emit('smart_output', {'type': 'ai_start', 'data': f'🤖 Running AI agent: {command}', 'mode': 'ai'})
        
        # Callback to stream progress
        def progress_callback(event_type: str, event_data: dict):
            if event_type == 'start':
                emit('smart_output', {'type': 'ai_progress', 'data': f'📋 Task: {event_data.get("task", "")}', 'mode': 'ai'})
            elif event_type == 'planning':
                emit('smart_output', {'type': 'ai_progress', 'data': f'💭 Planning step {event_data.get("step", "")}...', 'mode': 'ai'})
            elif event_type == 'plan':
                action = event_data.get('action', '')
                args = event_data.get('args', {})
                reason = event_data.get('reason', '')
                
                # Format the command that will be executed
                if action == 'shell':
                    cmd_str = args.get('command', '')
                elif action == 'ssh':
                    cmd_str = f"ssh {args.get('user','')}@{args.get('host','')} {args.get('command','')}"
                elif action == 'web_search':
                    cmd_str = f"search: {args.get('query', '')}"
                else:
                    cmd_str = f"{action}: {args}"
                
                emit('smart_output', {'type': 'ai_command', 'data': f'🔧 {cmd_str}', 'reason': reason, 'mode': 'ai'})
            elif event_type == 'executing':
                emit('smart_output', {'type': 'ai_progress', 'data': f'⚡ Executing: {event_data.get("action", "")}...', 'mode': 'ai'})
            elif event_type == 'result':
                result = event_data.get('result', '')[:150]
                emit('smart_output', {'type': 'ai_result', 'data': f'📤 Result: {result}', 'mode': 'ai'})
            elif event_type == 'success':
                emit('smart_output', {'type': 'ai_done', 'data': f'✅ Task completed!', 'mode': 'ai'})
            elif event_type == 'error':
                emit('smart_output', {'type': 'ai_error', 'data': f'❌ Error: {event_data.get("error", "")}', 'mode': 'ai'})
        
        try:
            result = run_autonomous(command, max_steps=5, callback=progress_callback)
            
            # Send final result
            if result.get('success'):
                emit('smart_output', {'type': 'ai_success', 'data': f'✅ SUCCESS: {result.get("result", "")[:300]}', 'mode': 'ai'})
            elif result.get('error'):
                emit('smart_output', {'type': 'ai_error', 'data': f'❌ {result.get("error", "")}', 'mode': 'ai'})
            else:
                emit('smart_output', {'type': 'ai_result', 'data': f'📊 {result.get("result", "")[:300]}', 'mode': 'ai'})
                
        except Exception as e:
            emit('smart_output', {'type': 'ai_error', 'data': f'❌ Error: {str(e)}', 'mode': 'ai'})


# === SSH Endpoints ===
@socketio.on('ssh_connect')
def handle_ssh_connect(data):
    """Connect to SSH server and start shell session"""
    server_name = data.get('server', '')
    password = data.get('password', '')  # Optional password from user
    shell_mode = data.get('shell_mode', False)  # Start interactive shell
    
    try:
        # Try to connect with provided password or stored credentials
        if password:
            # Create temporary server config with provided password
            server = ssh_manager._get_server(server_name)
            if server:
                server_copy = server.copy()
                server_copy['password'] = password
                # Temporarily update server config
                original_server = server.copy()
                ssh_manager.servers = [s if s['name'] != server_name else server_copy for s in ssh_manager.servers]
                
                if ssh_manager.connect(server_name):
                    ssh_connections[server_name] = True
                    emit('ssh_output', {'type': 'info', 'data': f'Connected to {server_name}'})
                    
                    # Start shell session if requested
                    if shell_mode:
                        start_ssh_shell(server_name)
                    
                    # Restore original config (without password)
                    ssh_manager.servers = [s if s['name'] != server_name else original_server for s in ssh_manager.servers]
                else:
                    emit('ssh_output', {'type': 'error', 'data': f'Failed to connect to {server_name}'})
                    ssh_manager.servers = [s if s['name'] != server_name else original_server for s in ssh_manager.servers]
            else:
                emit('ssh_output', {'type': 'error', 'data': f'Server {server_name} not found'})
        else:
            # Try normal connection (will prompt for password in CLI if needed)
            if ssh_manager.connect(server_name):
                ssh_connections[server_name] = True
                emit('ssh_output', {'type': 'info', 'data': f'Connected to {server_name}'})
                
                # Start shell session if requested
                if shell_mode:
                    start_ssh_shell(server_name)
            else:
                emit('ssh_output', {'type': 'password_required', 'data': f'Password required for {server_name}'})
    except Exception as e:
        emit('ssh_output', {'type': 'error', 'data': str(e)})


def start_ssh_shell(server_name):
    """Start an interactive SSH shell session"""
    if server_name not in ssh_manager.clients:
        return False
    
    client = ssh_manager.clients[server_name]
    
    try:
        # Start an interactive shell
        shell = client.invoke_shell()
        ssh_shells[server_name] = shell
        
        # Start a thread to read shell output
        def read_shell_output():
            while True:
                if server_name not in ssh_shells:
                    break
                    
                try:
                    # Read output with timeout
                    if shell.recv_ready():
                        data = shell.recv(4096).decode()
                        socketio.emit('ssh_output', {
                            'type': 'shell_output',
                            'data': data,
                            'server': server_name
                        })
                    elif shell.recv_stderr_ready():
                        data = shell.recv_stderr(4096).decode()
                        socketio.emit('ssh_output', {
                            'type': 'shell_error',
                            'data': data,
                            'server': server_name
                        })
                    else:
                        # Small delay to prevent busy waiting
                        import time
                        time.sleep(0.1)
                        
                        # Check if shell is still active
                        if shell.exit_status_ready():
                            socketio.emit('ssh_output', {
                                'type': 'shell_done',
                                'data': f'Shell session ended for {server_name}',
                                'server': server_name
                            })
                            break
                            
                except Exception as e:
                    socketio.emit('ssh_output', {
                        'type': 'error',
                        'data': f'Shell error: {str(e)}',
                        'server': server_name
                    })
                    break
        
        # Start the output reader thread
        import threading
        thread = threading.Thread(target=read_shell_output, daemon=True)
        thread.start()
        
        # Send initial prompt
        socketio.emit('ssh_output', {
            'type': 'shell_started',
            'data': f'Interactive shell started for {server_name}',
            'server': server_name
        })
        
        return True
        
    except Exception as e:
        socketio.emit('ssh_output', {
            'type': 'error',
            'data': f'Failed to start shell: {str(e)}',
            'server': server_name
        })
        return False


@socketio.on('ssh_shell_input')
def handle_ssh_shell_input(data):
    """Handle input to SSH shell session"""
    server_name = data.get('server', '')
    input_data = data.get('input', '')
    
    if server_name in ssh_shells:
        try:
            shell = ssh_shells[server_name]
            shell.send(input_data.encode())
        except Exception as e:
            emit('ssh_output', {'type': 'error', 'data': f'Shell input error: {str(e)}'})


@socketio.on('ssh_shell_exit')
def handle_ssh_shell_exit(data):
    """Exit SSH shell session"""
    server_name = data.get('server', '')
    
    if server_name in ssh_shells:
        try:
            shell = ssh_shells[server_name]
            shell.close()
            del ssh_shells[server_name]
            emit('ssh_output', {'type': 'info', 'data': f'Shell session closed for {server_name}'})
        except Exception as e:
            emit('ssh_output', {'type': 'error', 'data': f'Error closing shell: {str(e)}'})


@socketio.on('ssh_ai_command')
def handle_ssh_ai_command(data):
    """Generate AI commands for SSH troubleshooting"""
    server_name = data.get('server', '')
    ai_request = data.get('request', '')
    context = data.get('context', 'ssh_troubleshooting')
    
    try:
        # Create a specialized AI prompt for SSH commands
        prompt = f"""
        You are a Linux system administrator helping with SSH troubleshooting on server {server_name}.
        
        User request: {ai_request}
        
        Context: {context}
        
        Generate 3-5 specific Linux commands that would help address this request. 
        Each command should be:
        - Specific and executable
        - Safe for production systems
        - Relevant to troubleshooting SSH/Docker/Jitsi issues
        
        Return as JSON format:
        {{
            "commands": [
                {{
                    "command": "exact command here",
                    "explanation": "What this command does and why it's helpful"
                }}
            ]
        }}
        """
        
        # Use the autonomous agent to generate commands
        from agent.autonomous import run_autonomous
        
        def ai_callback(event_type: str, event_data: dict):
            # We'll handle the response differently for AI commands
            pass
        
        result = run_autonomous(prompt, max_steps=1, callback=ai_callback)
        
        # Try to parse the result as JSON commands
        try:
            import json
            if result.get('result'):
                # Extract JSON from the result
                result_text = result['result']
                if '{' in result_text and '}' in result_text:
                    # Find JSON portion
                    start = result_text.find('{')
                    end = result_text.rfind('}') + 1
                    json_str = result_text[start:end]
                    commands_data = json.loads(json_str)
                    emit('ssh_ai_response', commands_data)
                else:
                    # Fallback: create simple commands
                    emit('ssh_ai_response', {
                        'commands': [
                            {
                                'command': result['result'][:200],
                                'explanation': 'AI-generated command based on your request'
                            }
                        ]
                    })
            else:
                emit('ssh_ai_response', {'commands': []})
        except:
            emit('ssh_ai_response', {'commands': []})
            
    except Exception as e:
        emit('ssh_ai_response', {'commands': []})


@socketio.on('ssh_command')
def handle_ssh_command(data):
    """Execute SSH command (single command mode)"""
    server_name = data.get('server', '')
    command = data.get('command', '')
    
    # Send command echo
    emit('ssh_output', {'type': 'command', 'data': f'$ {command}'})
    
    try:
        result = ssh_manager.run_command(server_name, command)
        
        if 'error' in result:
            emit('ssh_output', {'type': 'error', 'data': result['error']})
        else:
            if result.get('stdout'):
                emit('ssh_output', {'type': 'output', 'data': result['stdout']})
            if result.get('stderr'):
                emit('ssh_output', {'type': 'error', 'data': result['stderr']})
            emit('ssh_output', {'type': 'done', 'data': f'Exit code: {result.get("exit_code", 0)}'})
            
    except Exception as e:
        emit('ssh_output', {'type': 'error', 'data': str(e)})


@socketio.on('ssh_disconnect')
def handle_ssh_disconnect(data):
    """Disconnect from SSH server"""
    server_name = data.get('server', '')
    
    # Close shell session if active
    if server_name in ssh_shells:
        try:
            ssh_shells[server_name].close()
            del ssh_shells[server_name]
        except:
            pass
    
    ssh_manager.disconnect(server_name)
    if server_name in ssh_connections:
        del ssh_connections[server_name]
    emit('ssh_output', {'type': 'info', 'data': f'Disconnected from {server_name}'})


# === Server Management ===
@app.route('/api/servers', methods=['GET'])
def list_servers():
    return jsonify({'servers': ssh_manager.list_servers()})


@app.route('/api/servers', methods=['POST'])
def add_server():
    data = request.json
    ssh_manager.add_server(
        name=data.get('name'),
        host=data.get('host'),
        user=data.get('user', 'root'),
        key_path=data.get('key_path'),
        password=data.get('password')
    )
    return jsonify({'status': 'ok'})


@app.route('/api/servers/<name>', methods=['DELETE'])
def delete_server(name):
    ssh_manager.remove_server(name)
    return jsonify({'status': 'ok'})


# === Memory Search ===
@app.route('/api/memory/search', methods=['GET'])
def search_memory():
    query = request.args.get('q', '')
    memory = get_memory()
    results = memory.search_conversations(query)
    return jsonify({'results': results})


@app.route('/api/memory', methods=['GET'])
def get_memory_history():
    memory = get_memory()
    results = memory.get_recent_conversations(limit=20)
    return jsonify({'conversations': results})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9000, allow_unsafe_werkzeug=True)