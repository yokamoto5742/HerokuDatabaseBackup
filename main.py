import datetime
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from service.backup_with_heroku_cli import backup_with_heroku_cli
from service.cleanup_old_backups import cleanup_old_backups
from utils.config_manager import load_config

JST = pytz.timezone('Asia/Tokyo')


class HerokuPostgreSQLBackup:
    def __init__(self):
        load_dotenv()
        config = load_config()
        backup_dir = config.get('Paths', 'backup_path')

        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL環境変数が設定されていません")

        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

        self.parsed_url = urlparse(self.database_url)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    load_dotenv()

    try:
        backup = HerokuPostgreSQLBackup()
        app_name = os.environ.get("HEROKU_APP_NAME")
        cleanup_old_backups(backup.backup_dir)
        backup_with_heroku_cli(backup.backup_dir, backup.timestamp, app_name)

    except Exception as e:
        print(f"❌ エラー: {e}")
