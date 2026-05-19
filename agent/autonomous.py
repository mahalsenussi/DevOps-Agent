"""
Autonomous Agent - Full autonomous loop with planner, executor, verifier
Implements: Plan → Execute → Verify → Fix → Repeat

Supports:
- Live step-by-step progress
- Callback for real-time updates
- Manual command fallback
"""
from typing import Optional, Dict, Any, List, Callable
import json

from .llm import get_llm
from .config import get_config
from .tools import ShellTool, WebSearchTool, FileSystemTool, SSHTool
from .memory import get_memory


# System prompts for each component
PLANNER_PROMPT = """You are a task planner. Given a task and history, determine the next step.

Task: {task}

History of steps:
{history}

What is the next step to complete this task? Respond in JSON:
{{"action": "tool_name", "args": {{"param": "value"}}, "reason": "why this action"}}

Available tools: shell, ssh, web_search, file_system

For SSH connections, use format:
{{"action": "ssh", "args": {{"host": "10.147.18.5", "user": "mahmoud", "password": "loraly", "command": "uptime"}}, "reason": "..."}}
"""

EXECUTOR_PROMPT = """You are a tool executor. Execute the planned action and return the result.

Action to execute: {action}
Arguments: {args}

Execute and return the result.
"""

VERIFIER_PROMPT = """You are a task verifier. Check if the task is complete.

Original task: {task}
Last result: {result}

Is the task complete? Respond with:
- SUCCESS: Task is done
- CONTINUE: More steps needed
- ERROR: Something went wrong

If ERROR, explain what needs to be fixed.
"""


class AutonomousAgent:
    """
    Full autonomous agent with multi-step loop:
    Planner → Executor → Verifier → Fixer → Repeat
    
    Supports callback for real-time progress updates
    """
    
    def __init__(self, max_steps: int = 10, callback: Optional[Callable] = None):
        self.max_steps = max_steps
        self.callback = callback
        self.llm = get_llm()
        
        # Available tools
        self.tools = {
            "shell": ShellTool(),
            "ssh": SSHTool(),
            "web_search": WebSearchTool(),
            "file_system": FileSystemTool()
        }
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Send progress update via callback"""
        if self.callback:
            try:
                self.callback(event_type, data)
            except:
                pass  # Ignore callback errors
    
    def run(self, task: str) -> Dict[str, Any]:
        """
        Run the full autonomous loop
        
        Returns:
            Dict with 'result', 'history', 'success' keys
        """
        # Emit start event
        self._emit("start", {"task": task})
        
        state = {
            "task": task,
            "history": [],
            "done": False,
            "success": False
        }
        
        for step in range(self.max_steps):
            # 1. PLAN
            self._emit("planning", {"step": step + 1})
            plan = self._planner(state)
            if not plan:
                break
            
            # Emit plan event
            self._emit("plan", {"step": step + 1, "action": plan.get("action"), "args": plan.get("args"), "reason": plan.get("reason", "")})
            
            # 2. EXECUTE
            self._emit("executing", {"step": step + 1, "action": plan.get("action")})
            result = self._executor(plan)
            
            # 3. VERIFY
            self._emit("verifying", {"step": step + 1})
            verification = self._verifier(state, result)
            
            # Record step
            step_record = {
                "step": step + 1,
                "plan": plan,
                "result": result,
                "verification": verification
            }
            state["history"].append(step_record)
            
            # Emit result event
            self._emit("result", {"step": step + 1, "result": result[:200], "verification": verification})
            
            # Check if done
            if "SUCCESS" in verification:
                state["done"] = True
                state["success"] = True
                self._emit("success", {"step": step + 1})
                break
            
            if "ERROR" in verification:
                state["done"] = True
                state["error"] = verification
                self._emit("error", {"step": step + 1, "error": verification})
                break
        
        # Final result
        if state["history"]:
            last_result = state["history"][-1]["result"]
            state["result"] = last_result
        else:
            state["result"] = "No steps executed"
        
        return state
    
    def _planner(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a plan for the next step"""
        task = state["task"]
        history = state.get("history", [])
        
        # Build history string
        history_str = ""
        for h in history[-3:]:  # Last 3 steps
            history_str += f"Step {h['step']}: {h['plan']} → {h['result'][:100]}...\n"
        
        if not history_str:
            history_str = "No previous steps"
        
        prompt = PLANNER_PROMPT.format(task=task, history=history_str)
        
        response = self.llm.invoke(prompt)
        content = self._extract_content(response)
        
        try:
            # Try to parse JSON
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
        except:
            pass
        
        return None
    
    def _executor(self, plan: Dict[str, Any]) -> str:
        """Execute the planned action"""
        action = plan.get("action", "")
        args = plan.get("args", {})
        
        if action in self.tools:
            tool = self.tools[action]
            
            # Build input from args
            if action == "shell":
                input_val = args.get("command", "")
            elif action == "web_search":
                input_val = args.get("query", "")
            elif action == "file_system":
                # Format: action:path
                file_action = args.get("action", "read")
                path = args.get("path", "")
                input_val = f"{file_action}:{path}"
            elif action == "ssh":
                # SSH needs special JSON format
                input_val = json.dumps(args)
            else:
                input_val = str(args)
            
            return tool._run(input_val)
        
        return f"Unknown action: {action}"
    
    def _verifier(self, state: Dict[str, Any], result: str) -> str:
        """Verify if the task is complete"""
        task = state["task"]
        
        prompt = VERIFIER_PROMPT.format(task=task, result=result[:500])
        response = self.llm.invoke(prompt)
        
        return self._extract_content(response)
    
    def _extract_content(self, response: Any) -> str:
        """Extract content from LLM response"""
        if hasattr(response, 'content'):
            return response.content
        return str(response)


# Convenience functions
def run_autonomous(task: str, max_steps: int = 10, callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Run an autonomous task with optional callback for progress updates"""
    agent = AutonomousAgent(max_steps=max_steps, callback=callback)
    return agent.run(task)