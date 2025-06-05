# Heroku PostgreSQL バックアップ用環境変数設定
# ファイル名: .env

# ===========================================
# データベース接続設定
# ===========================================
# HerokuのPostgreSQLデータベースURL
# Herokuダッシュボード > アプリ > Settings > Config Vars から取得
DATABASE_URL=postgresql://username:password@hostname:port/database?sslmode=require

# ===========================================
# Heroku設定
# ===========================================
# Herokuアプリ名
HEROKU_APP_NAME=your-app-name

# ===========================================
# バックアップ設定
# ===========================================
# バックアップ保存ディレクトリ
BACKUP_DIR=backups

# バックアップ保持期間（日数）
BACKUP_RETENTION_DAYS=30

# ===========================================
# 通知設定（オプション）
# ===========================================
# Slack Webhook URL（バックアップ結果通知用）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# メール通知設定
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=admin@example.com

# ===========================================
# PostgreSQL クライアント設定
# ===========================================
# pg_dumpのパス（Windowsの場合）
# PostgreSQLをインストールした場合のパス例
PG_DUMP_PATH=C:\Program Files\PostgreSQL\15\bin\pg_dump.exe
PG_PSQL_PATH=C:\Program Files\PostgreSQL\15\bin\psql.exe
