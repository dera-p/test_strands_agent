"""
Test script for AgentCore Runtime invocation
"""
import boto3
import json
import uuid

# Initialize the bedrock-agentcore client (runtime operations)
client = boto3.client('bedrock-agentcore', region_name='ap-northeast-1')

# Runtime identifier (from CloudFormation output)
runtime_arn = "arn:aws:bedrock-agentcore:ap-northeast-1:290473375544:runtime/StrandsPPTXAgent-jPTzxO9vHt"

# Generate a session ID
session_id = str(uuid.uuid4())

# Test prompt
test_prompt = "富士山についてのPowerPointプレゼンテーションを作成してください。3スライドで、基本情報、歴史と文化、登山情報を含めてください。"

print(f"Testing AgentCore Runtime: {runtime_arn}")
print(f"Session ID: {session_id}")
print(f"Prompt: {test_prompt}\n")

try:
    # Invoke the AgentCore Runtime with correct parameters
    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        contentType='application/json',
        accept='application/json',
        payload=json.dumps({
            "prompt": test_prompt,
            "model": {
                "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0"
            }
        }).encode('utf-8')
    )
    
    print("Successfully invoked AgentCore Runtime!")
    print(f"Response Status: {response['ResponseMetadata']['HTTPStatusCode']}\n")
    
    # Process the response stream
    print("Agent Response Stream:")
    print("=" * 80)
    
    if 'response' in response:
        # Read the streaming response
        body_stream = response['response']
        
        try:
            # Read the full content
            content = body_stream.read()
            if isinstance(content, bytes):
                print(content.decode('utf-8'))
            else:
                print(content)
        except Exception as stream_error:
            print(f"Stream read error: {stream_error}")
    
except Exception as e:
    print(f"Error invoking AgentCore Runtime: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more details
    if hasattr(e, 'response'):
        print(f"Response: {e.response}")
