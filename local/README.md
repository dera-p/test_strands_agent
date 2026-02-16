# Local Development

このディレクトリには、ローカル環境でエージェントを開発・テストするためのファイルが含まれています。

## セットアップ

### 初回環境構築

```bash
# Python仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存関係のインストール
python local/setup_pptx_env.py
```

### ローカル実行

```bash
# エージェントをローカルで実行
python local/my_pptx_agent.py
```

## ファイル説明

- **setup_pptx_env.py**: ローカル開発環境の初期セットアップスクリプト
  - Python依存関係のインストール
  - Node.js依存関係のインストール
  - Playwrightブラウザのインストール

- **my_pptx_agent.py**: ローカルでエージェントを直接実行するスクリプト
  - インタラクティブなCLIインターフェース
  - デバッグ・開発用

## 注意事項

- AWS認証情報が設定されている必要があります（Bedrock APIアクセス用）
- Node.js 16以上がインストールされている必要があります
