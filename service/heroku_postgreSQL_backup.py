import datetime
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from service.backup_data_as_csv import backup_data_as_csv
from service.backup_data_as_json import backup_data_as_json
from service.backup_with_heroku_cli import backup_with_heroku_cli
from utils.config_manager import load_config

JST = pytz.timezone('Asia/Tokyo')
logger = logging.getLogger(__name__)


class HerokuPostgreSQLBackup:
    def __init__(self) -> None:
        load_dotenv()
        config = load_config()
        backup_dir = config.get('Paths', 'backup_path')

        self.database_url: str = os.environ.get("DATABASE_URL", "")
        if not self.database_url:
            logger.error("DATABASE_URL環境変数が設定されていません")
            raise ValueError("DATABASE_URL環境変数が設定されていません")

        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
            logger.info("DATABASE_URLをpostgresql://形式に変換しました")

        self.parsed_url = urlparse(self.database_url)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")
        logger.info(f"HerokuPostgreSQLBackupを初期化しました - タイムスタンプ: {self.timestamp}")
        logger.info(f"バックアップディレクトリ: {self.backup_dir.absolute()}")


    def backup_with_cli(self, app_name: str) -> bool:
        return backup_with_heroku_cli(self.backup_dir, self.timestamp, app_name)

    def backup_as_json(self) -> bool:
        return backup_data_as_json(self.database_url, self.backup_dir, self.timestamp)

    def backup_as_csv(self) -> bool:
        return backup_data_as_csv(self.database_url, self.backup_dir, self.timestamp)

    def backup_all(self, app_name: str | None = None) -> dict[str, bool]:
        logger.info(f"バックアップ開始 - {self.timestamp}")
        logger.info(f"バックアップディレクトリ: {self.backup_dir.absolute()}")

        results = {}

        if app_name:
            logger.info(f"Heroku CLIバックアップを実行します - アプリ名: {app_name}")
            results['heroku_cli'] = self.backup_with_cli(app_name)
        else:
            logger.warning("Heroku app名が指定されていないため、Heroku CLIバックアップをスキップ")
            results['heroku_cli'] = False

        logger.info("JSONバックアップを実行します")
        results['json'] = self.backup_as_json()

        logger.info("CSVバックアップを実行します")
        results['csv'] = self.backup_as_csv()

        logger.info("バックアップ結果:")
        for method, success in results.items():
            status = "成功" if success else "失敗"
            logger.info(f"  {method}: {status}")
            status_emoji = "✅ 成功" if success else "❌ 失敗"

        return results
