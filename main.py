import datetime
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from config_manager import load_config

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

    def cleanup_old_backups(self, days=None):
        if days is None:
            config = load_config()
            days = config.getint('Backup', 'cleanup_days', fallback=30)
        try:
            current_time = datetime.datetime.now(JST)
            cutoff_time = current_time - datetime.timedelta(days=days)

            deleted_count = 0
            for backup_file in self.backup_dir.glob("*.dump"):
                file_ctime = datetime.datetime.fromtimestamp(
                    backup_file.stat().st_ctime,
                    tz=JST
                )

                if file_ctime < cutoff_time:
                    try:
                        backup_file.unlink()
                        print(f"🗑️  古いバックアップファイルを削除: {backup_file.name}")
                        deleted_count += 1
                    except OSError as e:
                        print(f"❌ ファイル削除エラー {backup_file.name}: {e}")

            if deleted_count > 0:
                print(f"✅ {deleted_count}個の古いバックアップファイルを削除しました")
            else:
                print("📂 削除対象の古いバックアップファイルはありませんでした")

        except Exception as e:
            print(f"❌ バックアップファイル削除エラー: {e}")

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
        backup.cleanup_old_backups()
        backup.backup_with_heroku_cli(app_name)

    except Exception as e:
        print(f"❌ エラー: {e}")
