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


    def backup_data_as_json(self):
        try:
            database_url = self.database_url
            if "?" in database_url:
                database_url += "&sslmode=require"
            else:
                database_url += "?sslmode=require"

            engine = create_engine(database_url)

            backup_data = {}
            tables = ['app_settings', 'prompts', 'summary_usage']

            print("🔄 データをJSONでバックアップ中...")

            with engine.connect() as conn:
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT * FROM {table}"))
                        rows = []
                        for row in result:
                            row_dict = dict(row._mapping)
                            # datetime オブジェクトを文字列に変換
                            for key, value in row_dict.items():
                                if isinstance(value, datetime.datetime):
                                    row_dict[key] = value.isoformat()
                            rows.append(row_dict)
                        backup_data[table] = rows
                        print(f"  ✅ {table}: {len(rows)}件")
                    except Exception as e:
                        print(f"  ❌ {table}: {e}")

            backup_file = self.backup_dir / f"data_backup_{self.timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            print(f"✅ JSONバックアップ完了: {backup_file}")
            return True

        except Exception as e:
            print(f"❌ JSONバックアップエラー: {e}")
            return False

    def backup_data_as_csv(self):
        try:
            database_url = self.database_url
            if "?" in database_url:
                database_url += "&sslmode=require"
            else:
                database_url += "?sslmode=require"

            engine = create_engine(database_url)

            tables = ['app_settings', 'prompts', 'summary_usage']
            csv_dir = self.backup_dir / f"csv_backup_{self.timestamp}"
            csv_dir.mkdir(exist_ok=True)

            print("🔄 データをCSVでバックアップ中...")

            for table in tables:
                try:
                    df = pd.read_sql_table(table, engine)
                    csv_file = csv_dir / f"{table}.csv"
                    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                    print(f"  ✅ {table}: {len(df)}件 -> {csv_file}")
                except Exception as e:
                    print(f"  ❌ {table}: {e}")

            print(f"✅ CSVバックアップ完了: {csv_dir}")
            return True

        except Exception as e:
            print(f"❌ CSVバックアップエラー: {e}")
            return False

    def backup_all(self, app_name=None):
        print(f"🚀 バックアップ開始 - {self.timestamp}")
        print(f"📁 バックアップディレクトリ: {self.backup_dir.absolute()}")

        results = {}

        if app_name:
            results['heroku_cli'] = self.backup_with_heroku_cli(app_name)
        else:
            print("⚠️ Heroku app名が指定されていないため、Heroku CLIバックアップをスキップ")
            results['heroku_cli'] = False

        results['pg_dump'] = self.backup_with_pg_dump()
        results['json'] = self.backup_data_as_json()
        results['csv'] = self.backup_data_as_csv()

        print("\n📊 バックアップ結果:")
        for method, success in results.items():
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"  {method}: {status}")

        successful_methods = sum(results.values())
        print(f"\n🎯 {successful_methods}/4 の方法で成功")

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
            backup.backup_with_heroku_cli(app_name)
        elif choice == "2":
            backup.backup_data_as_json()
        elif choice == "3":
            backup.backup_data_as_csv()
        elif choice == "4":
            app_name = os.environ.get("HEROKU_APP_NAME")
            backup.backup_all(app_name if app_name else None)
        else:
            print("❌ 無効な選択です")

    except Exception as e:
        print(f"❌ エラー: {e}")
