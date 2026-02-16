"""
Test script for AgentCore Runtime with template functionality
"""
import boto3
import json
import uuid
import os

# Initialize the bedrock-agentcore client (runtime operations)
region = os.environ.get('AWS_REGION', 'ap-northeast-1')
client = boto3.client('bedrock-agentcore', region_name=region)

# Runtime identifier (from CloudFormation output or environment variable)
runtime_arn = os.environ.get('AGENT_RUNTIME_ARN')
if not runtime_arn:
    raise ValueError("AGENT_RUNTIME_ARN environment variable is required. Set it to your AgentCore Runtime ARN.")

# Generate a session ID
session_id = str(uuid.uuid4())

# Test prompt for template usage - with detailed replacement instructions
test_prompt = """templates/business_template.pptxを編集して新しいプレゼンテーションを作成してください。

【重要指示】以下を順番に実行：

1. テンプレートダウンロード:
aws s3 cp s3://[YOUR_BUCKET]/templates/business_template.pptx /tmp/business_template.pptx

2. 完全なインベントリ抽出（JSON出力）:
python /app/skills/pptx/scripts/inventory.py /tmp/business_template.pptx /tmp/inventory.json

3. inventory.jsonの内容を確認:
cat /tmp/inventory.json

4. inventory.jsonをBASEとして、slide-0のshape-0とshape-1のみを以下に変更したreplacements.jsonを作成:
- slide-0 > shape-0 > paragraphs[0] > text: "AI駆動型ビジネス変革"
- slide-0 > shape-1 > paragraphs[0] > text: "2026年の戦略と実践"
【重要】slide-1からslide-4は元のinventory.jsonの内容をそのままコピーしてください

5. replace.py実行:
python /app/skills/pptx/scripts/replace.py /tmp/business_template.pptx /tmp/replacements.json /tmp/edited_business_template.pptx

6. S3アップロード:
upload_to_s3で /tmp/edited_business_template.pptx を presentations/ にアップロード

最終的なS3 URLを教えてください。"""

print(f"Testing AgentCore Runtime with Template: {runtime_arn}")
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
                "modelId": "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
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
            full_response = body_stream.read()
            print(full_response.decode('utf-8'))
        except Exception as e:
            print(f"Error reading stream: {e}")
    else:
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    print("=" * 80)
    print("\n✓ Test completed successfully")

except Exception as e:
    print(f"Error invoking AgentCore Runtime: {e}")
    import traceback
    traceback.print_exc()
