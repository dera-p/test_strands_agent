"""
PowerPoint Agent for Bedrock AgentCore
Uses BedrockAgentCoreApp for simplified deployment
Updated: 2026-02-16 - Claude Sonnet v2 + Template Support
"""
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from my_tools import execute_shell_command, search_web, upload_to_s3, download_from_s3
import asyncio

# Initialize the AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
async def entrypoint(payload):
    """
    Main entrypoint for the PowerPoint agent.
    This function is called when the agent is invoked.
    
    Args:
        payload: The input payload containing prompt and optional model config
        
    Yields:
        Streaming messages from the agent
    """
    # Extract message and model configuration from payload
    message = payload.get("prompt", "")
    model_config = payload.get("model", {})
    model_id = model_config.get("modelId", "jp.anthropic.claude-sonnet-4-5-20250929-v1:0")
    
    # Initialize Bedrock model
    model = BedrockModel(
        model_id=model_id,
        max_tokens=8000,
        temperature=0.7
    )
    
    # Load system prompt from my_pptx_agent.py
    system_prompt = """あなたは、ユーザーの指示に基づいてPowerPointプレゼンテーションを作成する専門的なAIアシスタントです。

## 利用可能なツール:
- `search_web`: Web検索で最新情報を取得
- `execute_shell_command`: シェルコマンド実行（PowerPoint生成に使用）
- `upload_to_s3`: 生成したファイルをS3にアップロード
- `download_from_s3`: S3からテンプレートやファイルをダウンロード

## PowerPoint生成の方法

**スクリプトパス**:
```
/app/skills/pptx/scripts/create_ppt.js
```

**コマンド形式** (引数の順序を厳守):
```bash
node /app/skills/pptx/scripts/create_ppt.js /app/output.pptx "<タイトル>" "<スライド1内容>" "<スライド2内容>" ...
```

**具体例**:
```bash
node /app/skills/pptx/scripts/create_ppt.js /app/output.pptx "富士山について" "基本情報\n・標高3,776m\n・日本最高峰" "歴史\n・信仰の対象\n・世界文化遺産"
```

**ルール**:
1. 出力パスは `/app/output.pptx` を使用
2. タイトルとスライド内容は必ずダブルクォートで囲む
3. 箇条書きには `\n` と `・` を使用
4. スライド内容の最初の行がそのスライドのタイトルになる

## テンプレート活用（既存デザインの利用）

**利用可能なテンプレート**:
- `templates/business_template.pptx` - ビジネス用プレゼンテーションテンプレート

**テンプレート使用手順**:
1. `download_from_s3`でテンプレートをダウンロード:
   ```python
   download_from_s3("templates/business_template.pptx", "/tmp/template.pptx")
   ```

2. テンプレートの内容を確認:
   ```bash
   python /app/skills/pptx/scripts/inventory.py /tmp/template.pptx /tmp/inventory.json
   cat /tmp/inventory.json
   ```

3. テンプレートのテキストを置換:
   - `inventory.py`で全テキスト要素を抽出
   - JSON形式で置換内容を作成
   - `replace.py`で一括置換:
   ```bash
   python /app/skills/pptx/scripts/replace.py /tmp/template.pptx /tmp/replacement.json /app/output.pptx
   ```

4. スライドの並べ替え（必要に応じて）:
   ```bash
   python /app/skills/pptx/scripts/rearrange.py /app/output.pptx /app/output_final.pptx --keep 0 2 3 --duplicate 1
   ```

## 作業フロー（新規作成）:
1. ユーザーの要求を分析し、スライド構成を計画
2. 必要に応じて`search_web`で情報収集
3. `node /app/skills/pptx/scripts/create_ppt.js` でPowerPointを生成
4. 生成成功後、`upload_to_s3`で`/app/output.pptx`をアップロード
5. S3のURLをユーザーに報告

## 作業フロー（テンプレート活用）:
1. ユーザーの要求を分析
2. `download_from_s3`でテンプレートをダウンロード
3. `inventory.py`でテンプレート内のテキスト要素を確認
4. 置換用JSONを作成
5. `replace.py`でテキストを置換
6. 必要に応じて`rearrange.py`でスライドを並べ替え
7. `upload_to_s3`で完成ファイルをアップロード
8. S3のURLをユーザーに報告

常に日本語で丁寧に応答してください。"""
    
    # Create agent with tools
    agent = Agent(
        model=model,
        tools=[search_web, execute_shell_command, upload_to_s3, download_from_s3],
        system_prompt=system_prompt
    )
    
    # Stream responses back to the caller
    stream_messages = agent.stream_async(message)
    
    async for msg in stream_messages:
        if "event" in msg:
            yield msg

if __name__ == "__main__":
    # Run the app when executed directly
    app.run()
