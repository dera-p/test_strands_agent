"""
PowerPoint Agent for Bedrock AgentCore Runtime
Module entrypoint for agent execution
"""
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_tools import execute_shell_command, search_web

# Initialize the AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload):
    """
    Main entrypoint for the PowerPoint agent.
    This function is called when the agent is invoked via AgentCore Runtime.
    
    Args:
        payload: The input payload containing prompt and optional model config
        
    Yields:
        Streaming messages from the agent
    """
    # Extract message and model configuration from payload
    message = payload.get("prompt", "")
    model_config = payload.get("model", {})
    model_id = model_config.get("modelId", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    
    # Initialize Bedrock model
    model = BedrockModel(
        model_id=model_id,
        max_tokens=8000,
        temperature=0.7
    )
    
    # Load system prompt
    system_prompt = """あなたは、ユーザーの指示に基づいてPowerPointプレゼンテーションを作成する専門的なAIアシスタントです。

## あなたの役割:
1. プレゼンテーションの構成を考案
2. 必要な情報を収集（Web検索を活用）
3. PowerPointファイルを生成（シェルコマンド実行）
4. 結果をユーザーに報告

## 利用可能なツール:
- `search_web`: Web検索で最新情報を取得
- `execute_shell_command`: Node.jsスクリプトでPowerPoint生成

## 作業フロー:
1. ユーザーの要求を分析
2. 必要に応じてWeb検索で情報収集
3. PowerPoint生成スクリプトを実行
4. 結果を報告

常に日本語で丁寧に応答してください。"""
    
    # Create agent with tools
    agent = Agent(
        model=model,
        tools=[search_web, execute_shell_command],
        system_prompt=system_prompt
    )
    
    # Stream responses back to the caller
    stream_messages = agent.stream_async(message)
    
    async for msg in stream_messages:
        if "event" in msg:
            yield msg

# For local testing
if __name__ == "__main__":
    app.run()
