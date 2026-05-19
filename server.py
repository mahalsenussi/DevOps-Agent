"""
FastAPI Server with WebSocket Terminal Support

Provides:
- REST API for agent operations
- WebSocket terminal for live command execution
- WebSocket SSH terminal for remote server control
"""
import asyncio
import subprocess
import json
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import our agent modules
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent import get_agent, run_autonomous, SSHManager

app = FastAPI(title="DevOps Agent API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSH Manager instance
ssh_manager = SSHManager()


# === WebSocket Terminal for local commands ===
@app.websocket("/ws/terminal")
async def terminal(websocket: WebSocket):
    """WebSocket terminal for streaming local command output"""
    await websocket.accept()
    
    try:
        while True:
            command = await websocket.receive_text()
            
            # Send command echo
            await websocket.send_json({
                "type": "command",
                "content": command
            })
            
            # Run command and stream output
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
                    await websocket.send_json({
                        "type": "output",
                        "content": line
                    })
            
            # Send completion
            await websocket.send_json({
                "type": "done",
                "exit_code": process.returncode
            })
            
    except WebSocketDisconnect:
        pass


# === WebSocket SSH Terminal ===
@app.websocket("/ws/ssh/{server_name}")
async def ssh_terminal(websocket: WebSocket, server_name: str):
    """WebSocket terminal for SSH remote command execution"""
    await websocket.accept()
    
    # Connect to server
    if not ssh_manager.connect(server_name):
        await websocket.send_json({
            "type": "error",
            "content": f"Failed to connect to {server_name}"
        })
        await websocket.close()
        return
    
    try:
        while True:
            command = await websocket.receive_text()
            
            # Send command echo
            await websocket.send_json({
                "type": "command",
                "content": command
            })
            
            # Run SSH command
            result = ssh_manager.run_command(server_name, command)
            
            if "error" in result:
                await websocket.send_json({
                    "type": "error",
                    "content": result["error"]
                })
            else:
                await websocket.send_json({
                    "type": "output",
                    "content": result.get("stdout", "")
                })
                if result.get("stderr"):
                    await websocket.send_json({
                        "type": "error",
                        "content": result["stderr"]
                    })
                await websocket.send_json({
                    "type": "done",
                    "exit_code": result.get("exit_code", 0)
                })
                
    except WebSocketDisconnect:
        ssh_manager.disconnect(server_name)


# === REST API Endpoints ===

@app.get("/")
async def root():
    return {"message": "DevOps Agent API", "version": "1.0.0"}


@app.get("/servers")
async def list_servers():
    """List configured SSH servers"""
    return {"servers": ssh_manager.list_servers()}


@app.post("/servers")
async def add_server(
    name: str,
    host: str,
    user: str = "root",
    key_path: Optional[str] = None,
    password: Optional[str] = None
):
    """Add a new SSH server"""
    ssh_manager.add_server(name, host, user, key_path, password)
    return {"status": "ok", "server": name}


@app.post("/agent/run")
async def run_agent_task(task: str, autonomous: bool = False):
    """Run an agent task"""
    if autonomous:
        result = run_autonomous(task)
    else:
        agent = get_agent()
        result = agent.run(task)
    
    return {"status": "ok", "result": result}


@app.post("/ssh/run")
async def run_ssh_command(server: str, command: str):
    """Run a command on an SSH server"""
    result = ssh_manager.run_command(server, command)
    return result


@app.get("/memory/search")
async def search_memory(query: str, limit: int = 5):
    """Search agent memory"""
    from agent.memory import get_memory
    memory = get_memory()
    results = memory.search_conversations(query, limit)
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)