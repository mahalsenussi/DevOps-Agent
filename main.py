"""
DevOps Agent - Main Entry Point

A real autonomous agent system powered by Ollama + LangGraph

Usage:
    python main.py "task"           # Run agent task
    python main.py -s "command"     # Run shell command
    python main.py -I               # Interactive mode
    python main.py --server        # Start API server
    python main.py --config        # Show config
"""
import argparse
import os
import sys
from typing import Optional

from agent import get_agent
from agent.config import get_config, update_config


def main():
    """Main entry point for the DevOps Agent"""
    parser = argparse.ArgumentParser(
        description="DevOps Agent - Autonomous server management with Ollama"
    )
    
    parser.add_argument(
        "task",
        nargs="?",
        help="Task to execute"
    )
    
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Ollama model to use (default: llama3)"
    )
    
    parser.add_argument(
        "--max-iterations",
        "-i",
        type=int,
        default=10,
        help="Maximum iterations (default: 10)"
    )
    
    parser.add_argument(
        "--max-tool-calls",
        "-t",
        type=int,
        default=5,
        help="Maximum tool calls per iteration (default: 5)"
    )
    
    parser.add_argument(
        "--interactive",
        "-I",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--shell",
        "-s",
        action="store_true",
        help="Execute shell commands directly (no LLM)"
    )
    
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start the API server with WebSocket terminal"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        action="store_true",
        help="Show current configuration"
    )
    
    args = parser.parse_args()
    
    # Show config
    if args.config:
        config = get_config()
        print("Current Configuration:")
        print(f"  Ollama URL: {config.ollama_base_url}")
        print(f"  Model: {config.ollama_model}")
        print(f"  Max Iterations: {config.max_iterations}")
        print(f"  Max Tool Calls: {config.max_tool_calls}")
        print(f"  Memory Enabled: {config.memory_enabled}")
        print(f"  Memory Dir: {config.memory_persist_dir}")
        return
    
    # Interactive mode
    if args.interactive:
        run_interactive(
            model=args.model,
            max_iterations=args.max_iterations,
            max_tool_calls=args.max_tool_calls
        )
        return
    
    # Shell mode (direct command execution)
    if args.shell:
        if not args.task:
            print("Error: Shell mode requires a command", file=sys.stderr)
            sys.exit(1)
        
        from agent.tools import run_shell
        result = run_shell(args.task)
        print(result)
        return
    
    # Server mode
    if args.server:
        import uvicorn
        from server import app
        print("Starting API server on http://localhost:8000")
        print("WebSocket terminal: ws://localhost:8000/ws/terminal")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return
    
    # Task mode
    if not args.task:
        parser.print_help()
        return
    
    run_task(
        task=args.task,
        model=args.model,
        max_iterations=args.max_iterations,
        max_tool_calls=args.max_tool_calls
    )


def run_task(
    task: str,
    model: Optional[str] = None,
    max_iterations: int = 10,
    max_tool_calls: int = 5
) -> None:
    """Run a single task with the agent"""
    print(f"🤖 DevOps Agent - Processing task...")
    print(f"   Task: {task}")
    print()
    
    # Update config if model provided
    if model:
        update_config(ollama_model=model)
    
    # Create agent
    agent = get_agent(
        model=model,
        max_iterations=max_iterations,
        max_tool_calls=max_tool_calls
    )
    
    # Run the agent
    try:
        result = agent.run(task)
        print("=" * 60)
        print("📝 RESULT:")
        print("=" * 60)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_interactive(
    model: Optional[str] = None,
    max_iterations: int = 10,
    max_tool_calls: int = 5
) -> None:
    """Run the agent in interactive mode"""
    print("🤖 DevOps Agent - Interactive Mode")
    print("   Type 'exit' or 'quit' to exit")
    print("   Type 'help' for available commands")
    print()
    
    # Update config if model provided
    if model:
        update_config(ollama_model=model)
    
    # Create agent
    agent = get_agent(
        model=model,
        max_iterations=max_iterations,
        max_tool_calls=max_tool_calls
    )
    
    while True:
        try:
            task = input("\n🎯 Task> ").strip()
            
            if not task:
                continue
            
            if task.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            if task.lower() in ["help", "h", "?"]:
                print("""
Available commands:
  exit/quit    - Exit the agent
  help         - Show this help
  clear        - Clear conversation history
  config       - Show current configuration

Just type a task and press Enter to execute it.
                """)
                continue
            
            if task.lower() == "clear":
                from agent.memory import get_memory
                get_memory().clear_conversations()
                print("Conversation history cleared.")
                continue
            
            # Execute the task
            result = agent.run(task)
            print("\n📝 RESULT:")
            print("-" * 40)
            print(result)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()