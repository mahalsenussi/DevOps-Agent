"""
File System Tool - Read, write, and manage files
"""
import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import BaseTool


class FileSystemTool(BaseTool):
    """Tool for file system operations"""
    
    name: str = "file_system"
    description: str = """Manage files on the server. Use this for:
    - Reading file contents (cat, type)
    - Listing directory contents (ls, dir)
    - Checking if files or directories exist
    - Getting file information (size, permissions)
    
    Input should be a file path or directory path."""
    
    def _run(self, args: str) -> str:
        """Perform file system operations
        
        Args:
            args: String in format "action:path" (e.g., "read:/etc/hosts")
        """
        try:
            # Parse action and path
            parts = args.split(":", 1)
            if len(parts) == 2:
                action, path = parts
            else:
                action = "read"
                path = args
            
            p = Path(path)
            
            if action == "read":
                if not p.exists():
                    return f"Error: File '{path}' does not exist"
                if p.is_dir():
                    return f"Error: '{path}' is a directory, use 'list' action"
                return p.read_text(encoding='utf-8')
            
            elif action == "list":
                if not p.exists():
                    return f"Error: Directory '{path}' does not exist"
                if not p.is_dir():
                    return f"Error: '{path}' is not a directory"
                
                items = []
                for item in sorted(p.iterdir()):
                    item_type = "DIR" if item.is_dir() else "FILE"
                    size = item.stat().st_size if item.is_file() else 0
                    items.append(f"{item_type:6} {size:10} {item.name}")
                
                return "\n".join(items) if items else "Directory is empty"
            
            elif action == "exists":
                return f"{'True' if p.exists() else 'False'}"
            
            elif action == "info":
                if not p.exists():
                    return f"Error: Path '{path}' does not exist"
                
                stat = p.stat()
                info = [
                    f"Path: {path}",
                    f"Type: {'Directory' if p.is_dir() else 'File'}",
                    f"Size: {stat.st_size} bytes",
                    f"Permissions: {oct(stat.st_mode)[-3:]}",
                    f"Modified: {stat.st_mtime}",
                ]
                return "\n".join(info)
            
            else:
                return f"Error: Unknown action '{action}'. Use: read, list, exists, info"
                
        except PermissionError:
            return f"Error: Permission denied accessing '{path}'"
        except Exception as e:
            return f"Error: {str(e)}"


# Convenience functions for direct use
def read_file(path: str) -> str:
    """Read a file's contents"""
    tool = FileSystemTool()
    return tool._run(f"read:{path}")


def list_directory(path: str) -> str:
    """List directory contents"""
    tool = FileSystemTool()
    return tool._run(f"list:{path}")


def file_exists(path: str) -> bool:
    """Check if a file or directory exists"""
    tool = FileSystemTool()
    return tool._run(f"exists:{path}") == "True"


def file_info(path: str) -> str:
    """Get file information"""
    tool = FileSystemTool()
    return tool._run(f"info:{path}")