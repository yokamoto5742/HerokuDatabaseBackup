import datetime
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from backup_data_as_csv import backup_data_as_csv
from backup_data_as_json import backup_data_as_json
from backup_with_heroku_cli import backup_with_heroku_cli
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


    def backup_with_heroku_cli_method(self, app_name):
        return backup_with_heroku_cli(self.backup_dir, self.timestamp, app_name)


    def backup_data_as_json_method(self):
        return backup_data_as_json(self.database_url, self.backup_dir, self.timestamp)

    def backup_data_as_csv_method(self):
        return backup_data_as_csv(self.database_url, self.backup_dir, self.timestamp)

    def backup_all(self, app_name=None):
        print(f"🚀 バックアップ開始 - {self.timestamp}")
        print(f"📁 バックアップディレクトリ: {self.backup_dir.absolute()}")

        results = {}

        if app_name:
            results['heroku_cli'] = self.backup_with_heroku_cli_method(app_name)
        else:
            print("⚠️ Heroku app名が指定されていないため、Heroku CLIバックアップをスキップ")
            results['heroku_cli'] = False

        results['json'] = self.backup_data_as_json_method()
        results['csv'] = self.backup_data_as_csv_method()

        print("\n📊 バックアップ結果:")
        for method, success in results.items():
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"  {method}: {status}")

        successful_methods = sum(results.values())
        print(f"\n🎯 {successful_methods}/3 の方法で成功")

        return results


if __name__ == "__main__":
    load_dotenv()

    print("🗄️ Heroku PostgreSQL バックアップツール")
    print("=" * 50)

    try:
        backup = HerokuPostgreSQLBackup()

        print("\n💡 利用可能なバックアップ方法:")
        print("1. Heroku CLI バックアップ (推奨)")
        print("2. JSON データバックアップ")
        print("3. CSV データバックアップ")
        print("4. すべての方法で実行")

        choice = input("\n選択してください (1-4): ").strip()

        if choice == "1":
            app_name = os.environ.get("HEROKU_APP_NAME")
            backup.backup_with_heroku_cli_method(app_name)
        elif choice == "2":
            backup.backup_data_as_json_method()
        elif choice == "3":
            backup.backup_data_as_csv_method()
        elif choice == "4":
            app_name = os.environ.get("HEROKU_APP_NAME")
            backup.backup_all(app_name if app_name else None)
        else:
            print("❌ 無効な選択です")

    except Exception as e:
        print(f"❌ エラー: {e}")
