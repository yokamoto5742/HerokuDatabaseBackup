# CHANGELOG

すべての重要な変更をこのファイルに記録します。
形式は[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に準拠しています。

## [Unreleased]

## [1.0.1] - 2025-11-30

### Fixed
- `service/heroku_postgreSQL_backup.py` の未使用変数エラーを修正: ログ出力で `status_emoji` 変数を正しく使用するように変更

## [1.0.0] - 2025-11-29

### Added
- HerokuPostgreSQLBackupクラス: Heroku PostgreSQLの包括的なバックアップツール
- 3つのバックアップ方式のサポート
  - Heroku CLI バックアップ（公式.dumpファイル）
  - JSONデータエクスポート（タイムゾーン対応）
  - CSVデータエクスポート（pandas利用）
- 自動クリーンアップ機能: 設定日数を超過した古いバックアップの削除
- リストア機能: 既存バックアップからの自動復元スクリプト生成
- 詳細なロギングシステムと自動ログローテーション機能
- Heroku認証チェック機能（ログイン状態確認と再ログイン）
- インタラクティブバックアップUI（`scripts/full_backup_script.py`）
- PyInstaller対応: Windows実行可能ファイル生成
- JST（日本標準時）タイムゾーン対応

### Configuration
- `utils/config.ini`: 集約された設定管理
  - バックアップディレクトリパス
  - 自動クリーンアップ期間
  - バックアップ対象テーブル指定
  - ログ設定（ディレクトリ、保持期間、ログレベル）
- `.env`: 環境変数管理（DATABASE_URL、HEROKU_APP_NAME）

### Development
- Pytestベースの包括的なテストスイート
- Pyrightによる型チェック設定
- PEP8準拠のコーディング規約
- PyInstallerビルドスクリプト

### Documentation
- `docs/README.md`: 日本語の包括的なプロジェクト説明書
- `docs/CHANGELOG.md`: 本ファイル（変更履歴）
- `CLAUDE.md`: 開発者向けプロジェクトガイドライン

## 主な技術スタック

- Python 3.12
- SQLAlchemy 2.0.44
- psycopg2（PostgreSQL接続ドライバ）
- pandas 2.3.3（CSVデータ操作）
- pytz 2025.2（タイムゾーン処理）
- python-dotenv 1.2.1（環境変数管理）
