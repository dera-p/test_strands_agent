# PowerPoint Agent on AWS Bedrock AgentCore

AWS Bedrock AgentCore Runtime上で動作するPowerPoint生成・編集AIエージェントです。Claude Sonnet 4.5を使用して、日本語で対話しながらプレゼンテーションファイルを作成・編集できます。

## 特徴

- 🤖 **Claude Sonnet 4.5**: 最新のAIモデルで高品質な内容生成
- 📊 **新規作成**: テキストから新しいプレゼンテーションを生成
- ✏️ **テンプレート編集**: 既存のPPTXファイルを編集・カスタマイズ
- ☁️ **S3統合**: 自動的にS3にアップロード・ダウンロード
- 🐳 **コンテナ**: AWS Lambda Python 3.13 ARM64環境で実行

## アーキテクチャ

```
User → AWS Bedrock AgentCore Runtime → Lambda Container (Python 3.13)
                                           ├── Claude Sonnet 4.5 (推論)
                                           ├── pptxgenjs (新規作成)
                                           ├── python-pptx (編集)
                                           └── S3 (ファイル保存)
```

## 前提条件

- AWS CLI設定済み
- AWS CDK v2インストール済み
- Python 3.11以上
- Node.js 16以上
- Docker Desktop（ローカルビルド/テスト用）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/dera-p/test_strands_agent.git
cd test_strands_agent
```

### 2. Python仮想環境の作成

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
# CDK用
pip install -r requirements-cdk.txt

# ローカル開発用（オプション）
python local/setup_pptx_env.py
```

## デプロイ

### AWS環境へのデプロイ

```bash
# CDK Bootstrap（初回のみ）
cdk bootstrap

# デプロイ
cdk deploy

# 出力からRuntime ARNとS3バケット名を確認
```

デプロイ後、以下の情報が出力されます：
- `RuntimeArn`: AgentCore RuntimeのARN
- `OutputBucketName`: PPTX出力用S3バケット名

### 環境変数の設定

```bash
# テスト実行に必要
export AGENT_RUNTIME_ARN="arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/YOUR_RUNTIME"
export AWS_REGION="ap-northeast-1"
```

## 使い方

### 基本的なテスト

新規プレゼンテーション作成：

```bash
cd tests
python test_agentcore.py
```

### テンプレート編集

1. S3にテンプレートをアップロード：

```bash
aws s3 cp your_template.pptx s3://YOUR_BUCKET/templates/business_template.pptx
```

2. テンプレート編集テストを実行：

```bash
python tests/test_template_agentcore.py
```

### ローカル開発

```bash
# ローカルでエージェントを直接実行
python local/my_pptx_agent.py
```

詳細は[local/README.md](local/README.md)を参照してください。

## プロジェクト構成

```
.
├── agent/                       # エージェントモジュール
├── agentskills/                 # スキル定義フレームワーク
├── docker/                      # Dockerファイル
│   └── Dockerfile.agentcore    # AgentCore用Dockerfile
├── infra/                       # AWS CDKインフラコード
│   └── stack.py                # CloudFormationスタック定義
├── local/                       # ローカル開発ツール
│   ├── my_pptx_agent.py        # ローカル実行用スクリプト
│   └── setup_pptx_env.py       # 環境セットアップ
├── skills/                      # スキル実装
│   └── pptx/                   # PowerPointスキル
│       ├── scripts/            # JS/Pythonスクリプト
│       │   ├── create_ppt.js  # 新規作成
│       │   ├── inventory.py   # テキスト抽出
│       │   └── replace.py     # テキスト置換
│       └── ooxml/             # OOXML仕様
├── tests/                       # テストスクリプト
├── utils/                       # ユーティリティ
├── agentcore_entrypoint.py     # エントリポイント
├── my_tools.py                 # ツール実装
└── app.py                      # CDKアプリ
```

## 機能詳細

### 新規作成

プロンプトを送信すると、AIが内容を生成してPowerPointファイルを作成します：

```python
prompt = "富士山についてのプレゼンテーションを3スライドで作成してください"
```

### テンプレート編集

既存のPPTXファイルをベースに、特定の箇所だけを編集：

1. `inventory.py`: テンプレートのテキスト要素を全て抽出
2. `replace.py`: JSONで指定した箇所のテキストを置換
3. その他のスライドは元のまま保持

### 利用可能なツール

- `execute_shell_command`: シェルコマンド実行
- `upload_to_s3`: S3へファイルアップロード
- `download_from_s3`: S3からファイルダウンロード
- `search_web`: Web検索（情報収集）

## トラブルシューティング

### Docker Buildエラー

Playwright Chromiumのインストールでエラーが出る場合、[docker/Dockerfile.agentcore](docker/Dockerfile.agentcore)の該当行がコメントアウトされていることを確認してください（現在のPPTX機能では不要）。

### S3アクセスエラー

IAMロールに適切なS3権限が付与されているか確認してください。CDKスタックで自動設定されます。

### Bedrockモデルアクセスエラー

AWS Bedrockコンソールで、使用するモデル（Claude Sonnet 4.5等）へのアクセスを有効化してください。

## ライセンス

このプロジェクトは実験的なものです。

## 貢献

Issue、Pull Requestを歓迎します。

## 参考資料

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [pptxgenjs](https://gitbrent.github.io/PptxGenJS/)
- [python-pptx](https://python-pptx.readthedocs.io/)
