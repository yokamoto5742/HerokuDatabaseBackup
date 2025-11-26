# Heroku PostgreSQL バックアップツール

HerokuのPostgreSQLデータベースを複数の形式でバックアップし、復元スクリプトを自動生成するPythonアプリケーションです。

## 🎯 目的

- Heroku上のPostgreSQLデータベースの定期的なバックアップ
- 複数のバックアップ形式（Heroku CLI、JSON、CSV）による冗長性確保
- 古いバックアップファイルの自動削除
- 簡単な復元プロセスの提供

## ✨ 主な機能

### バックアップ機能
1. **Heroku CLIバックアップ** - Heroku公式のバックアップ機能を使用
2. **JSONデータバックアップ** - 指定テーブルのデータをJSON形式で保存
3. **CSVデータバックアップ** - 指定テーブルのデータをCSV形式で保存
4. **古いバックアップ削除** - 設定した日数以上古いファイルを自動削除

### 復元機能
- バックアップ時に復元スクリプトを自動生成
- 対話式の復元プロセス
- 復元前の安全確認
- 復元後のデータベース状態確認

## 📋 必要な環境

### システム要件
- Python 3.11
- Windows OS（設定ファイルのパスがWindows形式）
- Heroku CLI

### 必要なライブラリ
```
pandas==2.0.3
psycopg2-binary==2.9.10
python-dotenv==1.1.0
pytz==2025.2
SQLAlchemy==2.0.41
```

### 外部ツール
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)がインストールされていること
- Herokuアカウントにログインしていること

## 🚀 セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
`.env`ファイルを作成し、以下の変数を設定：

```env
DATABASE_URL=postgresql://username:password@hostname:port/database
HEROKU_APP_NAME=your-heroku-app-name
```

### 3. 設定ファイルの編集
`config.ini`ファイルでバックアップディレクトリと保持期間を設定：

```ini
[Paths]
backup_path = C:\Users\your-username\path\to\backup\directory

[Backup]
cleanup_days = 30
```

### 4. Heroku CLIのセットアップ
```bash
# Heroku CLIインストール後
heroku login
heroku auth:whoami  # ログイン確認
```

## 📖 使用方法

### 対話式バックアップ
```bash
python full_backup_script.py
```

メニューから選択：
- `1`: Heroku CLIバックアップのみ
- `2`: JSONデータバックアップのみ  
- `3`: CSVデータバックアップのみ
- `4`: すべての方法で実行

### 自動バックアップ
```bash
python main.py
```
- Heroku CLIバックアップのみ実行
- 古いバックアップファイルを自動削除

### 復元スクリプト生成
```bash
python create_restore_script.py
```
- 既存のバックアップファイルから復元スクリプトを生成
- 対話式でダンプファイルを選択

## 🔧 設定オプション

### config.ini
```ini
[Paths]
backup_path = バックアップファイルの保存ディレクトリ

[Backup]
cleanup_days = 古いバックアップファイルの保持日数（デフォルト: 30日）
```

### 環境変数
- `DATABASE_URL`: PostgreSQLデータベースの接続URL
- `HEROKU_APP_NAME`: HerokuアプリケーションName

## 🛠️ トラブルシューティング

### よくある問題

#### 1. "DATABASE_URL環境変数が設定されていません"
- `.env`ファイルが正しく作成されているか確認
- `DATABASE_URL`が正しく設定されているか確認

#### 2. "Heroku CLIが見つかりません"
- Heroku CLIがインストールされているか確認
- `heroku --version`でインストール状況を確認
- パスが通っているか確認

#### 3. "heroku pg:backups:download失敗"
- Herokuアプリにアクセス権限があるか確認
- `heroku apps`でアプリ一覧を確認
- アプリ名が正しいか確認

#### 4. "設定ファイルが見つかりません"
- `config.ini`ファイルがスクリプトと同じディレクトリにあるか確認
- ファイルのエンコーディングがUTF-8になっているか確認

## 🔒 セキュリティ注意事項

- `.env`ファイルにはデータベース認証情報が含まれるため、バージョン管理に含めないでください
- バックアップファイルには機密データが含まれる可能性があるため、適切に管理してください
- 復元操作は既存データを完全に上書きするため、十分注意してください

## ライセンス
LICENSEファイルを参照

## 📞 サポート

技術的な問題や質問がある場合は、以下を確認してください：
1. このREADMEのトラブルシューティングセクション
2. Heroku公式ドキュメント
3. 各ライブラリの公式ドキュメント