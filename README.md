# DevOps Agent

An autonomous DevOps agent system powered by Ollama and LangGraph for intelligent server management and automation.

## 🚀 Features

- **Autonomous Task Execution**: Execute complex DevOps tasks using AI reasoning
- **Shell Command Execution**: Direct shell command execution with safety controls
- **Interactive Mode**: Interactive chat interface for task management
- **API Server**: RESTful API with WebSocket terminal support
- **Memory System**: Persistent conversation and task memory
- **Tool Integration**: Extensible tool system for various operations
- **Multi-Model Support**: Compatible with various Ollama models

## 📊 Architecture

```
agent/
├── main.py              # Main entry point
├── server.py            # API server with WebSocket
├── webapp.py            # Web interface
├── agent/               # Agent core logic
│   ├── config.py        # Configuration management
│   ├── memory.py        # Memory system
│   └── tools/           # Tool implementations
├── templates/           # HTML templates
├── data/                # Data storage
└── requirements.txt     # Python dependencies
```

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Ollama installed and running
- Virtual environment (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/mahalsenussi/DevOps-Agent.git
cd DevOps-Agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama (if not already installed)
# Visit: https://ollama.ai/

# Pull required model
ollama pull llama3
```

## 🚀 Usage

### Command Line

```bash
# Run a single task
python main.py "check disk usage on /var"

# Run with specific model
python main.py "restart nginx service" --model llama3

# Run in interactive mode
python main.py -I

# Execute shell command directly
python main.py -s "ls -la"

# Start API server
python main.py --server

# Show configuration
python main.py --config
```

### Interactive Mode

```bash
python main.py -I
```

Available commands in interactive mode:
- `exit/quit` - Exit the agent
- `help` - Show help
- `clear` - Clear conversation history
- `config` - Show current configuration

### API Server

```bash
python main.py --server
```

The API server runs on `http://localhost:8000` with WebSocket terminal at `ws://localhost:8000/ws/terminal`.

## 📡 API Endpoints

- `GET /` - Web interface
- `POST /api/task` - Execute a task
- `WS /ws/terminal` - WebSocket terminal

## ⚙️ Configuration

Configuration is managed through `agent/config.py`:

```python
# Default configuration
ollama_base_url = "http://localhost:11434"
ollama_model = "llama3"
max_iterations = 10
max_tool_calls = 5
memory_enabled = True
memory_persist_dir = "data/memory"
```

## 🔌 Tools

The agent includes various tools for:
- Shell command execution
- File system operations
- System monitoring
- Service management
- Network operations

## 📝 Dependencies

```
langgraph>=0.0.20
langchain>=0.1.0
ollama>=0.1.0
fastapi>=0.100.0
uvicorn>=0.23.0
websockets>=11.0
python-dotenv>=1.0.0
```

## 🧪 Testing

```bash
# Test password prompt
python test_password_prompt.py

# Test SSH shell
python test_ssh_shell.py
```

## 🚧 Production Deployment

For production deployment:

1. Use a production WSGI server (Gunicorn)
2. Implement proper authentication
3. Add rate limiting
4. Configure logging and monitoring
5. Use environment variables for sensitive data
6. Set up proper error handling

## 🔒 Security

- Shell command execution with safety controls
- Input validation and sanitization
- Configurable tool access permissions
- Memory encryption for sensitive data

## 📧 Support

For questions or support, please open an issue in the repository.

## 📄 License

This project is developed for DevOps automation and server management purposes.

---

**Note**: This agent executes shell commands and should be used with caution. Always review tasks before execution in production environments.
