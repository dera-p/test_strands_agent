from strands import tool
import subprocess

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
