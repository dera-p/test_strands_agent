from strands import tool
import subprocess
import json
import boto3
import os
from datetime import datetime
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


@tool
def upload_to_s3(file_path: str, bucket_name: str = None, s3_key: str = None) -> str:
    """Upload a file to S3 bucket.
    
    Args:
        file_path: Path to the file to upload
        bucket_name: S3 bucket name (optional, uses default if not specified)
        s3_key: S3 object key (optional, auto-generated if not specified)
        
    Returns:
        S3 URL or error message
    """
    try:
        # Use default bucket if not specified
        if bucket_name is None:
            bucket_name = os.environ.get('S3_BUCKET_NAME', 'strands-pptx-output')
        
        # Auto-generate S3 key if not specified
        if s3_key is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = os.path.basename(file_path)
            s3_key = f"presentations/{timestamp}-{filename}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # Generate URL
        region = os.environ.get('AWS_REGION', 'ap-northeast-1')
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        
        return f"Successfully uploaded to S3:\nBucket: {bucket_name}\nKey: {s3_key}\nURL: {s3_url}"
        
    except Exception as e:
        return f"S3 Upload Error: {e}"
