"""
Core Agent - Simple ReAct agent implementation (without LangGraph)
"""
from typing import Optional, List, Dict, Any
import json

from .llm import OllamaClient, get_llm
from .config import get_config
from .tools import ShellTool, WebSearchTool, FileSystemTool
from .memory import get_memory


# System prompt for the agent
AGENT_SYSTEM_PROMPT = """You are an autonomous DevOps agent. Think step by step and complete the task.

You have access to these tools:
- shell: Execute shell commands (use for system commands, file operations)
- web_search: Search the web for information
- file_system: Read files or list directories

When you need to use a tool, respond in this exact JSON format:
{"action": "tool_name", "input": "what to pass to the tool"}

When you have the answer, respond with:
{"action": "final_answer", "input": "your answer here"}

Example:
Task: Check system uptime
Thought: I need to run the uptime command
Action: shell
Input: uptime
"""


class DevOpsAgent:
    """Main DevOps Agent class - Simple ReAct loop"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        max_iterations: int = 5,
        max_tool_calls: int = 3
    ):
        config = get_config()
        
        # Override config if provided
        if model:
            config.ollama_model = model
        
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        
        # Initialize LLM and tools
        self.llm = get_llm()
        self.tools = {
            "shell": ShellTool(),
            "web_search": WebSearchTool(),
            "file_system": FileSystemTool()
        }
    
    def run(self, task: str) -> str:
        """Run the agent with a task using a simple ReAct loop"""
        
        # Build initial prompt
        prompt = f"""Task: {task}

Think step by step. If you need to use a tool, respond with JSON like:
{{"action": "tool_name", "input": "tool input"}}

If you have the answer, respond with:
{{"action": "final_answer", "input": "your answer"}}

"""
        
        tool_call_count = 0
        iterations = 0
        
        while iterations < self.max_iterations and tool_call_count < self.max_tool_calls:
            iterations += 1
            
            # Get LLM response
            response = self.llm.invoke(prompt, system_prompt=AGENT_SYSTEM_PROMPT)
            
            # Extract content from response object
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse the response
            try:
                # Find JSON in response
                content = str(content)
                if "{" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        parsed = json.loads(json_str)
                        
                        action = parsed.get("action", "")
                        tool_input = parsed.get("input", "")
                        
                        # Check if this is a final answer
                        if action == "final_answer":
                            # Save to memory
                            config = get_config()
                            if config.memory_enabled:
                                memory = get_memory()
                                memory.add_conversation(user_input=task, agent_response=tool_input)
                            # Extract just the answer from the response object
                            if hasattr(tool_input, 'content'):
                                return tool_input.content
                            return str(tool_input)
                        
                        # Execute tool
                        if action in self.tools:
                            tool = self.tools[action]
                            tool_result = tool._run(tool_input)
                            tool_call_count += 1
                            
                            # Add result to prompt for next iteration
                            prompt += f"\n\nThought: I executed {action} with input '{tool_input}'\nResult: {tool_result}\n\nNow provide your next action or final answer:\n"
                        else:
                            prompt += f"\n\nThought: The action '{action}' is not recognized. Let me try again.\n\n"
                    else:
                        # No JSON found, just continue with the response
                        prompt += f"\n\nThought: {content}\n\nProvide your next action or final answer:\n"
                else:
                    prompt += f"\n\nThought: {content}\n\nProvide your next action or final answer:\n"
                    
            except json.JSONDecodeError as e:
                # If we can't parse JSON, treat the response as the answer
                if iterations >= self.max_iterations - 1:
                    return str(response)
                prompt += f"\n\nThought: {response}\n\nProvide your next action or final answer:\n"
        
        # Max iterations reached, return the last response
        return "I was unable to complete this task. Please try again with a more specific request."
    
    async def run_async(self, task: str) -> str:
        """Run the agent asynchronously (same as sync for now)"""
        return self.run(task)


# Convenience function to get an agent instance
def get_agent(
    model: Optional[str] = None,
    max_iterations: int = 5,
    max_tool_calls: int = 3
) -> DevOpsAgent:
    """Get a configured DevOps agent instance"""
    return DevOpsAgent(
        model=model,
        max_iterations=max_iterations,
        max_tool_calls=max_tool_calls
    )