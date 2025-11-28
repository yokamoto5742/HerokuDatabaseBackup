# Heroku PostgreSQL バックアップツール

Herokuホストの PostgreSQL データベースを複数のフォーマット（Heroku CLI、JSON、CSV）で自動バックアップし、古いバックアップを管理するPythonツールです

## 主な機能

- **Heroku CLI バックアップ**: 公式Heroku CLIを使用した完全なダンプファイル生成
- **JSON データエクスポート**: 指定テーブルをJSON形式でエクスポート（タイムゾーン対応）
- **CSV データエクスポート**: pandasを使用したCSV形式でのエクスポート
- **自動クリーンアップ**: 設定日数を超過した古いバックアップの自動削除
- **リストア機能**: 既存バックアップから復元スクリプトを自動生成
- **ロギングシステム**: 詳細な実行ログと自動ログローテーション
- **実行可能ファイル化**: PyInstallerを使用したWindows実行ファイル対応

## 必要な環境

### 開発環境
- Python 3.10以上
- pip

### 実行環境
- Python 3.10以上（開発実行時）
- Heroku CLI（Heroku CLIバックアップ使用時）
- PostgreSQL接続情報（DATABASE_URL環境変数）

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd HerokuDatabaseBackup
```

### 2. 仮想環境の作成
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
`.env`ファイルをプロジェクトルートに作成し、以下を設定します：
```env
DATABASE_URL=postgresql://user:password@host:port/database
HEROKU_APP_NAME=your-heroku-app-name
```

### 5. 設定ファイルの確認
`utils/config.ini`で以下の設定を確認・調整します：
```ini
[Paths]
backup_path = C:\Users\...\backups  # バックアップディレクトリ

[Backup]
cleanup_days = 30  # 保持期間（日数）

[Database]
backup_tables = app_settings,prompts,summary_usage  # バックアップ対象テーブル

[LOGGING]
log_directory = logs  # ログディレクトリ
log_retention_days = 30  # ログ保持期間（日数）
log_level = INFO  # ログレベル
```

## 使用方法

### 自動バックアップ実行
```bash
python main.py
```
Heroku CLI認証チェック → 古いバックアップ削除 → Heroku CLIでバックアップ作成の順序で実行

### インタラクティブバックアップ
```bash
python scripts/full_backup_script.py
```
以下から選択可能：
1. Heroku CLI バックアップ
2. JSON データバックアップ
3. CSV データバックアップ
4. すべての方法で実行

### リストアスクリプト生成
```bash
python scripts/create_restore_script.py
```
既存バックアップから自動復元スクリプトを生成し、ユーザーが対話的にファイルを選択可能

## プロジェクト構造

```
HerokuDatabaseBackup/
├── main.py                           # 自動バックアップエントリーポイント
├── build.py                          # PyInstaller実行可能ファイルビルド
├── requirements.txt                  # Python依存関係
├── .env                             # 環境変数設定（DATABASE_URL等）
│
├── service/                         # バックアップ処理メイン実装
│   ├── heroku_postgreSQL_backup.py   # HerokuPostgreSQLBackupクラス（メイン）
│   ├── backup_with_heroku_cli.py     # Heroku CLIバックアップ
│   ├── backup_data_as_json.py        # JSONエクスポート
│   ├── backup_data_as_csv.py         # CSVエクスポート
│   ├── cleanup_old_backups.py        # 古いバックアップ削除
│   └── heroku_login_again.py         # Heroku認証チェック
│
├── scripts/                         # スタンドアロンスクリプト
│   ├── full_backup_script.py         # インタラクティブバックアップUI
│   ├── create_restore_script.py      # リストアスクリプト生成
│   └── project_structure.py          # プロジェクト構造確認用
│
├── utils/                           # ユーティリティモジュール
│   ├── config_manager.py            # 設定ファイル管理
│   ├── config.ini                   # 設定ファイル
│   ├── database_helper.py           # データベース接続ヘルパー
│   └── log_rotation.py              # ログローテーション処理
│
├── tests/                           # テストスイート
│   ├── test_*.py                    # 各機能のユニットテスト
│   └── conftest.py                  # pytest設定
│
├── docs/                            # ドキュメント
│   ├── README.md                    # 本ファイル
│   └── LICENSE                      # ライセンス
│
└── logs/                            # 実行ログ（自動生成）
```

## アーキテクチャ概要

### HerokuPostgreSQLBackupクラス
`service/heroku_postgreSQL_backup.py`に定義される中心的なクラス

**主要メソッド**:
- `backup_with_cli(app_name)`: Heroku CLIでバックアップを取得
- `backup_as_json()`: テーブルをJSON形式でエクスポート
- `backup_as_csv()`: テーブルをCSV形式でエクスポート
- `backup_all(app_name)`: すべての方法でバックアップ実行

```python
# 使用例
backup = HerokuPostgreSQLBackup()
results = backup.backup_all("my-heroku-app")
```

### データベース接続
- DATABASE_URLから自動的に`postgresql://`形式に変換
- SSL接続要求（`sslmode=require`）を自動付与
- JST（日本標準時）タイムゾーンで処理

### バックアップ対象テーブル
設定により以下テーブルをバックアップ（デフォルト）:
- `app_settings`
- `prompts`
- `summary_usage`

`utils/config.ini`の`[Database]`セクション内の`backup_tables`で変更可能

### タイムスタンプフォーマット
すべてのバックアップファイルは`YYYYMMDD_HHMMSS`形式のタイムスタンプを使用します：
```
20251129_143022  # 2025年11月29日 14時30分22秒
```

## 開発者向け情報

### テスト実行
```bash
# すべてのテストを実行
python -m pytest tests/ -v --tb=short --disable-warnings

# 特定のテストファイルを実行
python -m pytest tests/test_backup_data_as_json.py -v

# カバレッジレポート付きで実行
python -m pytest --cov=. --cov-report=html
```

### 型チェック
```bash
# pyright設定に基づいて型チェック実行
pyright service/ utils/
```

### 実行可能ファイルのビルド
```bash
python build.py
```
生成されたファイル: `dist/HerokuDatabaseBackup.exe`（Windows環境）

PyInstaller実行時の自動処理：
- `.env`ファイルをバンドル
- `utils/config.ini`をバンドル
- 依存ライブラリを静的リンク

## トラブルシューティング

### Heroku CLIが見つからない
```
❌ Heroku CLIがインストールされていません
```
**解決策**: [Heroku CLI公式](https://devcenter.heroku.com/articles/heroku-cli)からインストール後、`heroku login`で認証を実行してください

### DATABASE_URLエラー
```
ERROR: DATABASE_URL環境変数が設定されていません
```
**解決策**: `.env`ファイルに有効な`DATABASE_URL`を設定し、`python -m dotenv list`で確認してください

### 設定ファイルが見つからない
```
設定ファイルが見つかりません: utils/config.ini
```
**解決策**: `utils/config.ini`が存在することを確認してください。存在しない場合は新規作成し、必須セクション（`[Paths]`、`[Backup]`等）を記述してください

### バックアップディレクトリのアクセス権限エラー
```
PermissionError: [Errno 13] Permission denied: 'C:\path\to\backups'
```
**解決策**: `utils/config.ini`の`backup_path`に書き込み可能なディレクトリパスを設定してください。Windows環境では相対パスではなく絶対パスの使用を推奨します

## 主要な依存関係

| パッケージ | 用途 |
|-----------|------|
| SQLAlchemy | データベース接続・ORM |
| psycopg2 | PostgreSQL接続ドライバ |
| pandas | CSVデータ操作 |
| pytz | タイムゾーン処理 |
| python-dotenv | 環境変数管理 |
| pyinstaller | 実行可能ファイル生成 |

詳細は`requirements.txt`を参照してください

## ライセンス

このプロジェクトのライセンスについては`docs/LICENSE`を参照してください
