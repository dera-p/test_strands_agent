from strands import tool
import subprocess
import json
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

@tool
def search_web(query: str) -> str:
    """Search the web for information using DuckDuckGo.
    
    Args:
        query: Search query
        
    Returns:
        Search results as string
    """
    if DDGS is None:
        return "Search tool not available: duckduckgo_search package missing."
        
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
        
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search Error: {e}"


@tool
def execute_shell_command(command: str) -> str:
    """Run a shell command.
    
    Args:
        command: Command to execute
        
    Returns:
        Output of the command
    """
    try:
        # Use shell=True for windows command compatibility
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', # Explicit encoding
            errors='replace'
        )
        
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n[Stderr]\n{result.stderr.strip()}"
            
        if result.returncode != 0:
            return f"Command fail (Exit {result.returncode}):\n{output}"
            
        return output if output else "(No output)"
        
    except Exception as e:
        return f"Execution Error: {e}"
