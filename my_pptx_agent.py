import asyncio
import sys
from pathlib import Path
import json
import subprocess

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from strands import Agent
# IMPORT NOTE: Do NOT import shell from strands_tools as it breaks on Windows (termios dependency)
from strands_tools import file_read, file_write 
from agentskills import discover_skills, create_skill_tool, generate_skills_prompt, get_bedrock_agent_model

# Import custom parser/events to bypass potential renderer issues
from utils.strands_stream.parser import StrandsEventParser
from utils.strands_stream.events import TextEvent, ToolStreamEvent, CurrentToolUseEvent, ToolResultEvent, ReasoningEvent

# --- Windows Compatible Tools ---

from my_tools import execute_shell_command as shell_cmd # Rename back to shell or keep verify




# --- Custom Renderer ---

class SimpleTerminalRenderer:
    def __init__(self):
        self.parser = StrandsEventParser()
    
    def reset(self):
        self.parser.reset()
        print("\n" + "-"*40 + "\n")
        
    def process(self, event):
        parsed_events = self.parser.parse(event)
        for e in parsed_events:
            if isinstance(e, TextEvent):
                print(e.data, end="", flush=True)
            elif isinstance(e, ReasoningEvent):
                print(f"\n[Thinking] {e.data}", end="", flush=True)
            elif isinstance(e, CurrentToolUseEvent):
                print(f"\n\n[Tool Use: {e.tool_name}]")
                if e.tool_input:
                    print(f"Input: {json.dumps(e.tool_input, ensure_ascii=False, indent=2)}")
            elif isinstance(e, ToolResultEvent):
                preview = e.data
                if len(preview) > 500:
                    preview = preview[:500] + "... (truncated)"
                print(f"\n[Tool Result] {preview}\n")
            elif isinstance(e, ToolStreamEvent):
                if e.data:
                    data_str = e.data if isinstance(e.data, str) else json.dumps(e.data, ensure_ascii=False)
                    print(f"[Tool Stream] {data_str}")

# --- Main Agent Logic ---

async def main():
    print("--- PowerPoint Agent (Local Phase 1 - Windows Compatible) ---")
    
    # 1. Discover Skills
    skills_dir = Path(__file__).parent / "skills"
    if not skills_dir.exists():
        print(f"Error: Skills directory not found at {skills_dir}")
        return
        
    skills = discover_skills(skills_dir)
    print(f"Loaded {len(skills)} skills.")
    
    # 2. Create Skill Tool
    skill_tool = create_skill_tool(skills, skills_dir)
    
    # 3. System Prompt
    base_prompt = """あなたはPowerPoint作成・編集の専門エージェントです。
`pptx` スキルを活用して、ユーザーの要望に応じたプレゼンテーションを作成します。

**重要な指示:**
1. **日本語対応**: ユーザーとの対話および、作成するスライドのコンテンツは原則として **日本語** を使用してください。
2. **スキル利用**: `skill` ツールを使用して `pptx` スキルの詳細な手順(Instructions)を読み込んでください。
3. **実行**: スキルの指示に従い、`shell` ツール等を使ってコマンドを実行し、成果物を作成してください。
4. **スクリプトパス**: PPTXスクリプトは `/app/skills/pptx/scripts/` にあります。
   - 例: `node /app/skills/pptx/scripts/create_ppt.js "タイトル" "内容"`
5. **ファイル出力**: PPTXファイルを生成したら、`upload_to_s3` ツールを使ってS3にアップロードしてください。
6. **エラー対応**: 依存関係のエラーが発生した場合は、その内容をユーザーに報告してください。
"""

    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n[Available Skills Metadata]\n{skills_prompt}"
    
    # 4. Create Agent
    agent_model = get_bedrock_agent_model(thinking=True)
    
    agent = Agent(
        system_prompt=full_prompt,
        tools=[skill_tool, file_read, file_write, shell_cmd],
        model=agent_model,
        callback_handler=None
    )
    
    print("\nPPTXエージェントが起動しました。")
    print("入力例: 'AIエージェントについてのスライドを3枚作成して'")
    print("'exit' で終了します。\n")
    
    renderer = SimpleTerminalRenderer()
    
    # Non-interactive mode for testing
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"\n[Non-Interactive] Prompt: {prompt}")
        renderer.reset()
        try:
             async for event in agent.stream_async(prompt):
                 renderer.process(event)
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        return

    # Interactive Loop
    while True:
        try:
            user_input = input("\nUser> ")
            if user_input.lower() in ("exit", "quit", "終了"):
                break
            if not user_input.strip():
                continue
            
            renderer.reset()
            async for event in agent.stream_async(user_input):
                 renderer.process(event)
                 
        except KeyboardInterrupt:
            print("\n終了します...")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
