import os

from dotenv import load_dotenv

from service.backup_with_heroku_cli import backup_with_heroku_cli
from service.cleanup_old_backups import cleanup_old_backups
from service.heroku_login_again import ensure_heroku_login
from service.heroku_postgreSQL_backup import HerokuPostgreSQLBackup


if __name__ == "__main__":
    load_dotenv()

    try:
        # Herokuログイン状態をチェック
        ensure_heroku_login()

        backup = HerokuPostgreSQLBackup()
        app_name = os.environ.get("HEROKU_APP_NAME")
        cleanup_old_backups(backup.backup_dir)
        backup_with_heroku_cli(backup.backup_dir, backup.timestamp, app_name)

    except Exception as e:
        print(f"❌ エラー: {e}")
