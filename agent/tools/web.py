"""
Web Search Tool - Search the web for information
"""
from typing import Optional
from langchain_core.tools import BaseTool


class WebSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo"""
    
    name: str = "web_search"
    description: str = """Search the web for information. Use this when you need to:
    - Look up documentation or how-to guides
    - Find solutions to technical problems
    - Get current information about technologies
    - Research topics you don't have knowledge of
    
    Input should be a search query string."""
    
    def _run(self, query: str, max_results: Optional[int] = None) -> str:
        """Search the web and return results"""
        from ..config import get_config
        from duckduckgo_search import DDGS
        
        config = get_config()
        max_results = max_results or config.web_search_max_results
        
        try:
            ddgs = DDGS()
            results = ddgs.text(query, max_results=max_results)
            
            if not results:
                return "No search results found."
            
            output = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("href", "No URL")
                body = result.get("body", "No description")
                
                output.append(f"{i}. {title}\n   URL: {url}\n   {body}\n")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error searching web: {str(e)}"


# Convenience function for direct use
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web directly"""
    tool = WebSearchTool()
    return tool._run(query, max_results)