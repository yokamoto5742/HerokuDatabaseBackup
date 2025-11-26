# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述し、文末に"。"や"."をつけないでください。

## Project Overview

Heroku PostgreSQL backup tool that creates database backups in multiple formats (Heroku CLI, JSON, CSV) with automatic cleanup of old backups and restore script generation.

## Development Commands

### Running Scripts
```bash
# Main automated backup (Heroku CLI + cleanup)
python main.py

# Interactive backup with multiple options
python service/full_backup_script.py

# Generate restore script from existing backup
python scripts/create_restore_script.py

# Build executable
python build.py
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v --tb=short --disable-warnings

# Run specific test file
python -m pytest tests/test_main.py -v
```

### Type Checking
Pyright is configured for service/ and utils/ directories only (tests/ and scripts/ are excluded).
```bash
# Check types with pyright
pyright service/ utils/
```

## Architecture

### Core Components

**HerokuPostgreSQLBackup Class (main.py & service/full_backup_script.py)**
- Entry point for all backup operations
- Manages database connection via `DATABASE_URL` environment variable
- Auto-converts `postgres://` to `postgresql://` for SQLAlchemy compatibility
- Uses JST timezone for all timestamps
- All backup operations use timestamps in `YYYYMMDD_HHMMSS` format

**Configuration System (utils/config_manager.py)**
- Centralizes configuration loading via `load_config()`
- Handles both development and PyInstaller-built executable environments
- Uses `sys._MEIPASS` for frozen executables
- Config location: `utils/config.ini`

**Backup Strategies**
1. `backup_with_heroku_cli()`: Official Heroku backups via CLI (creates .dump files)
2. `backup_data_as_json()`: Exports specified tables to JSON with datetime serialization
3. `backup_data_as_csv()`: Exports to CSV using pandas (creates timestamped directory)

**Restore System (scripts/create_restore_script.py)**
- `RestoreScriptGenerator` generates standalone Python restore scripts
- Generated scripts include safety confirmations and database reset
- Interactive file selection from available backups

### Key Patterns

**Database Connection**
Always append SSL mode to DATABASE_URL:
```python
database_url = self.database_url
if "?" in database_url:
    database_url += "&sslmode=require"
else:
    database_url += "?sslmode=require"
```

**Hardcoded Table Names**
The backup system targets these specific tables:
- `app_settings`
- `prompts`
- `summary_usage`

When modifying backup logic, ensure these table names are updated consistently across JSON and CSV backup methods.

**Import Path Differences**
- `service/full_backup_script.py` imports: `from config_manager import load_config` (relative)
- `main.py` imports: `from utils.config_manager import load_config` (absolute)
- `scripts/create_restore_script.py` imports: `from config_manager import load_config` (relative)

### Configuration Files

**config.ini**
```ini
[Paths]
backup_path = C:\Users\...\backups  # Windows path

[Backup]
cleanup_days = 14  # Days to keep old backups
```

**.env**
```
DATABASE_URL=postgresql://...
HEROKU_APP_NAME=your-app-name
```

### External Dependencies

**Heroku CLI**
Required for `heroku pg:backups:capture` and `heroku pg:backups:download` commands. Must be installed and authenticated before running backups.

**Windows-Specific**
The project is configured for Windows (paths, shell=True in subprocess calls). Be cautious when adapting for Unix-like systems.

## Important Notes

- Environment variables loaded via `python-dotenv` at runtime
- All subprocess Heroku commands use `shell=True` (Windows requirement)
- Backup file cleanup uses file creation time (st_ctime) with JST timezone
- PyInstaller build includes .env and config.ini in bundle
- Type checking excludes tests/ and scripts/ directories per pyrightconfig.json
