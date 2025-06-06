import csv
import datetime
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pytz
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BACKUP_DIR = r"C:\Users\yokam\OneDrive\HerokuDatabaseBackup\backups"
JST = pytz.timezone('Asia/Tokyo')


class HerokuPostgreSQLBackup:
    def __init__(self):
        load_dotenv()

        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL環境変数が設定されていません")

        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

        self.parsed_url = urlparse(self.database_url)
        self.backup_dir = Path(BACKUP_DIR)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")


    def backup_with_heroku_cli(self, app_name):
        try:
            backup_file = self.backup_dir / f"heroku_backup_{self.timestamp}.dump"

            print("🔄 Herokuバックアップを作成中...")
            subprocess.run([
                "heroku", "pg:backups:capture",
                "--app", app_name
            ], shell=True, check=True)

            print("🔄 バックアップをダウンロード中...")
            result = subprocess.run([
                "heroku", "pg:backups:download",
                "--app", app_name,
                "--output", str(backup_file)
            ], shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Herokuバックアップ完了: {backup_file}")
                return True
            else:
                print(f"❌ Herokuバックアップ失敗: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Herokuバックアップエラー: {e}")
            return False


if __name__ == "__main__":
    load_dotenv()

    try:
        backup = HerokuPostgreSQLBackup()
        app_name = os.environ.get("HEROKU_APP_NAME")
        backup.backup_with_heroku_cli(app_name)

    except Exception as e:
        print(f"❌ エラー: {e}")
