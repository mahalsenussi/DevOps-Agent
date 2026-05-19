"""
MCP Server - Model Context Protocol server for dynamic tool discovery

This enables the agent to discover and use tools dynamically,
similar to how Claude Desktop works.
"""
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class MCPTool:
    """Tool definition for MCP"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class MCPServer:
    """MCP Server for tool discovery and execution"""
    
    def __init__(self, name: str = "devops-agent"):
        self.name = name
        self.tools: Dict[str, MCPTool] = {}
        self._running = False
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Register a tool with the MCP server"""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        self.tools[name] = tool
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a specific tool"""
        return self.tools.get(name)
    
    def execute_tool(self, name: str, input_data: Any) -> Any:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        return tool.handler(input_data)
    
    def list_tools_json(self) -> str:
        """List all tools as JSON"""
        return json.dumps({"tools": self.get_tools()}, indent=2)


# Create default MCP server instance
_mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance"""
    return _mcp_server


# Example: Register system info tool
def system_info_handler(input_data: Any) -> Dict[str, Any]:
    """Handler for system info tool"""
    import platform
    return {
        "system": platform.system(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }


# Register default tools (can be extended)
def register_default_tools():
    """Register default DevOps tools with MCP"""
    mcp = get_mcp_server()
    
    # System info tool
    mcp.register_tool(
        name="system_info",
        description="Get system information",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=system_info_handler
    )


# Auto-register on import
register_default_tools()