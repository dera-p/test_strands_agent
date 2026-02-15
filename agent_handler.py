import json
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import agent (assuming my_pptx_agent.py exposes main or has reusable components)
from my_pptx_agent import Agent, discover_skills, create_skill_tool, generate_skills_prompt, get_bedrock_agent_model
from strands_tools import file_read, file_write
from my_tools import execute_shell_command as shell_cmd

# Setup skills once (optimization for warm starts)
SKILLS_DIR = Path(__file__).parent / "skills"
SKILLS = discover_skills(SKILLS_DIR)
SKILL_TOOL = create_skill_tool(SKILLS, SKILLS_DIR)
SKILLS_PROMPT = generate_skills_prompt(SKILLS)

BASE_PROMPT = """あなたはPowerPoint作成・編集の専門エージェントです。
`pptx` スキルを活用して、ユーザーの要望に応じたプレゼンテーションを作成します。

**重要な指示:**
1. **日本語対応**: ユーザーとの対話および、作成するスライドのコンテンツは原則として **日本語** を使用してください。
2. **スキル利用**: `skill` ツールを使用して `pptx` スキルの詳細な手順(Instructions)を読み込んでください。
3. **実行**: スキルの指示に従い、`shell` ツール等を使ってコマンドを実行し、成果物を作成してください。

**環境:** AWS Lambda (Container) 上で実行されています。
"""

FULL_PROMPT = f"{BASE_PROMPT}\n\n[Available Skills Metadata]\n{SKILLS_PROMPT}"

AGENT_MODEL = get_bedrock_agent_model(thinking=True)

# Build Agent
agent = Agent(
    system_prompt=FULL_PROMPT,
    tools=[SKILL_TOOL, file_read, file_write, shell_cmd], 
    model=AGENT_MODEL,
    callback_handler=None
)

def handler(event, context):
    """
    AWS Lambda Handler for Bedrock Agent Action Group or Direct Invocation.
    """
    print(f"Received event: {json.dumps(event)}")
    
    # 1. Parse Input
    # Support multiple event formats (Direct Invoke vs Bedrock Agent)
    user_input = ""
    if 'prompt' in event:
        # Direct Invocation for testing
        user_input = event['prompt']
    elif 'inputText' in event:
         # Simplified Bedrock Agent Event
         user_input = event['inputText']
    else:
        # Default fallback
        user_input = "AIエージェントのスライドを作成して"

    print(f"Processing input: {user_input}")

    # 2. Run Agent
    # For Lambda, we need to collect the stream result and return it as a single response
    # (unless using response streaming which is advanced setup)
    
    response_text = ""
    
    async def run_agent():
        nonlocal response_text
        try:
            async for event in agent.stream_async(user_input):
                 # Capture relevant text/tool outputs for final response
                 # For now, simplistic capture
                 if hasattr(event, 'data') and isinstance(event.data, str):
                     response_text += event.data
        except Exception as e:
            print(f"Agent Error: {e}")
            import traceback
            traceback.print_exc()
            response_text += f"\nError: {e}"

    # Run loop
    asyncio.run(run_agent())

    # 3. Return Response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Agent execution completed',
            'response': response_text
        }, ensure_ascii=False)
    }
