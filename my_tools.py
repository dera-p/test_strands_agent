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
        # Log the command being executed
        print(f"[execute_shell_command] Executing: {command}", flush=True)
        
        # Use shell=True for windows command compatibility
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', # Explicit encoding
            errors='replace',
            timeout=60  # 60 second timeout
        )
        
        print(f"[execute_shell_command] Exit code: {result.returncode}", flush=True)
        print(f"[execute_shell_command] Stdout length: {len(result.stdout)}", flush=True)
        print(f"[execute_shell_command] Stderr length: {len(result.stderr)}", flush=True)
        
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n[Stderr]\n{result.stderr.strip()}"
            
        if result.returncode != 0:
            error_msg = f"Command fail (Exit {result.returncode}):\n{output}"
            print(f"[execute_shell_command] ERROR: {error_msg}", flush=True)
            return error_msg
        
        print(f"[execute_shell_command] Success! Output: {output[:200]}...", flush=True)    
        return output if output else "(No output)"
        
    except subprocess.TimeoutExpired:
        error_msg = f"Command timeout after 60 seconds: {command}"
        print(f"[execute_shell_command] TIMEOUT: {error_msg}", flush=True)
        return error_msg
    except Exception as e:
        error_msg = f"Execution Error: {e}"
        print(f"[execute_shell_command] EXCEPTION: {error_msg}", flush=True)
        return error_msg


@tool
def upload_to_s3(file_path: str, bucket_name: str = None, s3_key: str = None) -> str:
    """Upload a file to S3 bucket.
    
    Args:
        file_path: Path to the file to upload
        bucket_name: S3 bucket name (optional, auto-detected if not specified)
        s3_key: S3 object key (optional, auto-generated if not specified)
        
    Returns:
        S3 URL or error message
    """
    try:
        print(f"[upload_to_s3] Starting upload...", flush=True)
        print(f"[upload_to_s3] File path: {file_path}", flush=True)
        print(f"[upload_to_s3] Bucket (requested): {bucket_name}", flush=True)
        
        # Function to check if bucket exists
        def bucket_exists(bucket):
            if bucket is None:
                return False
            try:
                s3_client = boto3.client('s3')
                s3_client.head_bucket(Bucket=bucket)
                print(f"[upload_to_s3] Bucket {bucket} exists", flush=True)
                return True
            except Exception as e:
                print(f"[upload_to_s3] Bucket {bucket} does not exist or access denied: {e}", flush=True)
                return False
        
        # Function to auto-detect bucket
        def auto_detect_bucket():
            try:
                print(f"[upload_to_s3] Attempting auto-detection...", flush=True)
                s3_client = boto3.client('s3')
                response = s3_client.list_buckets()
                
                # Look for bucket with 'strands-pptx-output' prefix
                for bucket in response.get('Buckets', []):
                    if bucket['Name'].startswith('strands-pptx-output'):
                        detected_bucket = bucket['Name']
                        print(f"[upload_to_s3] Auto-detected S3 bucket: {detected_bucket}", flush=True)
                        return detected_bucket
                
                print(f"[upload_to_s3] No bucket with 'strands-pptx-output' prefix found", flush=True)
                return None
            except Exception as e:
                print(f"[upload_to_s3] Auto-detection error: {e}", flush=True)
                return None
        
        # Auto-detect bucket if not specified or if specified bucket doesn't exist
        if bucket_name is None:
            # Try environment variable first
            bucket_name = os.environ.get('S3_BUCKET_NAME')
            print(f"[upload_to_s3] Env S3_BUCKET_NAME: {bucket_name}", flush=True)
        
        # Validate bucket exists, otherwise auto-detect
        if not bucket_exists(bucket_name):
            print(f"[upload_to_s3] Specified/env bucket invalid, attempting auto-detection...", flush=True)
            bucket_name = auto_detect_bucket()
        
        # Final validation
        if bucket_name is None:
            return "Error: No valid S3 bucket found. Please specify bucket_name parameter or create a bucket with 'strands-pptx-output' prefix."
        
        # Auto-generate S3 key if not specified
        if s3_key is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = os.path.basename(file_path)
            s3_key = f"presentations/{timestamp}-{filename}"
        
        print(f"[upload_to_s3] S3 key: {s3_key}", flush=True)
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"Error: File not found: {file_path}"
            print(f"[upload_to_s3] {error_msg}", flush=True)
            return error_msg
        
        # Get file size
        file_size = os.path.getsize(file_path)
        print(f"[upload_to_s3] Uploading {file_path} ({file_size} bytes) to s3://{bucket_name}/{s3_key}", flush=True)
        
        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # Generate URL
        region = os.environ.get('AWS_REGION', 'ap-northeast-1')
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        
        success_msg = f"Successfully uploaded to S3:\nBucket: {bucket_name}\nKey: {s3_key}\nURL: {s3_url}\nSize: {file_size} bytes"
        print(f"[upload_to_s3] {success_msg}", flush=True)
        return success_msg
        
    except Exception as e:
        import traceback
        error_msg = f"S3 Upload Error: {e}\n{traceback.format_exc()}"
        print(f"[upload_to_s3] ERROR: {error_msg}", flush=True)
        return error_msg


@tool
def download_from_s3(s3_key: str, local_path: str = None, bucket_name: str = None) -> str:
    """Download a file from S3 bucket.
    
    Args:
        s3_key: S3 object key (e.g., 'templates/business_template.pptx')
        local_path: Local file path to save (optional, auto-generated if not specified)
        bucket_name: S3 bucket name (optional, auto-detected if not specified)
        
    Returns:
        Local file path or error message
    """
    try:
        print(f"[download_from_s3] Starting download...", flush=True)
        print(f"[download_from_s3] S3 key: {s3_key}", flush=True)
        print(f"[download_from_s3] Bucket (requested): {bucket_name}", flush=True)
        
        # Function to auto-detect bucket (reuse logic from upload_to_s3)
        def auto_detect_bucket():
            try:
                print(f"[download_from_s3] Attempting auto-detection...", flush=True)
                s3_client = boto3.client('s3')
                response = s3_client.list_buckets()
                
                # Look for bucket with 'strands-pptx-output' prefix
                for bucket in response.get('Buckets', []):
                    if bucket['Name'].startswith('strands-pptx-output'):
                        detected_bucket = bucket['Name']
                        print(f"[download_from_s3] Auto-detected S3 bucket: {detected_bucket}", flush=True)
                        return detected_bucket
                
                print(f"[download_from_s3] No bucket with 'strands-pptx-output' prefix found", flush=True)
                return None
            except Exception as e:
                print(f"[download_from_s3] Auto-detection error: {e}", flush=True)
                return None
        
        # Auto-detect bucket if not specified
        if bucket_name is None:
            bucket_name = os.environ.get('S3_BUCKET_NAME')
            print(f"[download_from_s3] Env S3_BUCKET_NAME: {bucket_name}", flush=True)
            
            if bucket_name is None:
                bucket_name = auto_detect_bucket()
        
        # Final validation
        if bucket_name is None:
            return "Error: No valid S3 bucket found. Please specify bucket_name parameter."
        
        # Auto-generate local path if not specified
        if local_path is None:
            filename = os.path.basename(s3_key)
            local_path = f"/tmp/{filename}"
        
        print(f"[download_from_s3] Local path: {local_path}", flush=True)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download from S3
        s3_client = boto3.client('s3')
        print(f"[download_from_s3] Downloading s3://{bucket_name}/{s3_key} to {local_path}...", flush=True)
        s3_client.download_file(bucket_name, s3_key, local_path)
        
        # Get file size
        file_size = os.path.getsize(local_path)
        
        success_msg = f"Successfully downloaded from S3:\nBucket: {bucket_name}\nKey: {s3_key}\nLocal path: {local_path}\nSize: {file_size} bytes"
        print(f"[download_from_s3] {success_msg}", flush=True)
        return success_msg
        
    except Exception as e:
        import traceback
        error_msg = f"S3 Download Error: {e}\n{traceback.format_exc()}"
        print(f"[download_from_s3] ERROR: {error_msg}", flush=True)
        return error_msg
