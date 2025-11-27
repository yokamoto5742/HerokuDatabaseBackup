import logging
import os

from dotenv import load_dotenv

from service.backup_with_heroku_cli import backup_with_heroku_cli
from service.cleanup_old_backups import cleanup_old_backups
from service.heroku_login_again import ensure_heroku_login
from service.heroku_postgreSQL_backup import HerokuPostgreSQLBackup
from utils.config_manager import get_log_directory, get_log_retention_days
from utils.log_rotation import setup_logging


if __name__ == "__main__":
    load_dotenv()

    # ログシステムの初期化
    log_dir = get_log_directory()
    log_retention = get_log_retention_days()
    setup_logging(log_directory=log_dir, log_retention_days=log_retention)

    logger = logging.getLogger(__name__)

    try:
        logger.info("バックアップ処理を開始します")

        # Herokuログイン状態をチェック
        ensure_heroku_login()

        backup = HerokuPostgreSQLBackup()
        app_name = os.environ.get("HEROKU_APP_NAME")
        logger.info(f"Herokuアプリ: {app_name}")

        cleanup_old_backups(backup.backup_dir)
        backup_with_heroku_cli(backup.backup_dir, backup.timestamp, app_name)

        logger.info("バックアップ処理が正常に完了しました")

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
