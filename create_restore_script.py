import datetime
import os
import pytz
from pathlib import Path

from config_manager import load_config  # 追加

JST = pytz.timezone('Asia/Tokyo')

def get_backup_dir():
    config = load_config()
    return config.get('Paths', 'backup_path')


class RestoreScriptGenerator:
    def __init__(self, backup_dir=None, timestamp=None):
        self.backup_dir = Path(backup_dir or get_backup_dir())
        self.timestamp = timestamp or datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")

    def create_restore_script(self):
        """復元スクリプトを生成"""
        restore_script = f'''#!/usr/bin/env python3
# Heroku Dump復元スクリプト (Generated: {self.timestamp})

import os
import subprocess
import sys
from pathlib import Path

class HerokuDumpRestore:
    def __init__(self):
        self.backup_dir = Path(r"{self.backup_dir}")
        self.dump_file = self.backup_dir / "heroku_backup_{self.timestamp}.dump"

    def check_heroku_cli(self):
        """Heroku CLIがインストールされているかチェック"""
        try:
            result = subprocess.run(["heroku", "--version"],
                                  capture_output=True, text=True, shell=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_dump_file_exists(self):
        """ダンプファイルが存在するかチェック"""
        return self.dump_file.exists()

    def list_apps(self):
        """利用可能なHerokuアプリ一覧を表示"""
        try:
            result = subprocess.run(["heroku", "apps"],
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print("利用可能なHerokuアプリ:")
                print(result.stdout)
                return True
            else:
                print(f"アプリ一覧取得エラー: {{result.stderr}}")
                return False
        except Exception as e:
            print(f"アプリ一覧取得エラー: {{e}}")
            return False

    def restore_from_dump(self, app_name, confirm=True):
        """Heroku dumpファイルからデータベースを復元"""

        # 事前チェック
        if not self.check_heroku_cli():
            print("❌ Heroku CLIがインストールされていません")
            print("インストール: https://devcenter.heroku.com/articles/heroku-cli")
            return False

        if not self.check_dump_file_exists():
            print(f"❌ ダンプファイルが見つかりません: {{self.dump_file}}")
            return False

        if not app_name:
            print("❌ Herokuアプリ名が指定されていません")
            self.list_apps()
            return False

        # 確認プロンプト
        if confirm:
            print(f"⚠️  警告: アプリ '{{app_name}}' のデータベースを復元します")
            print(f"📁 ダンプファイル: {{self.dump_file}}")
            print("⚠️  既存のデータは完全に置き換えられます！")

            response = input("続行しますか？ (yes/no): ").lower()
            if response not in ['yes', 'y']:
                print("❌ 復元がキャンセルされました")
                return False

        try:
            # 既存のデータベースをリセット
            print("🔄 既存のデータベースをリセット中...")
            reset_result = subprocess.run([
                "heroku", "pg:reset", "DATABASE_URL",
                "--app", app_name,
                "--confirm", app_name
            ], shell=True, capture_output=True, text=True)

            if reset_result.returncode != 0:
                print(f"❌ データベースリセット失敗: {{reset_result.stderr}}")
                return False

            # ダンプファイルから復元
            print("🔄 ダンプファイルから復元中...")
            restore_cmd = f'heroku pg:psql --app {{app_name}} < "{{self.dump_file}}"'

            restore_result = subprocess.run(
                restore_cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if restore_result.returncode == 0:
                print("✅ 復元完了！")
                print("🔍 データベース状態を確認することをお勧めします")
                return True
            else:
                print(f"❌ 復元失敗: {{restore_result.stderr}}")
                return False

        except Exception as e:
            print(f"❌ 復元エラー: {{e}}")
            return False

    def verify_restore(self, app_name):
        """復元後のデータベース状態を確認"""
        try:
            print("🔍 データベース状態を確認中...")

            # テーブル一覧を取得
            tables_cmd = f'heroku pg:psql --app {{app_name}} -c "\\\\dt"'
            tables_result = subprocess.run(
                tables_cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if tables_result.returncode == 0:
                print("📊 データベーステーブル:")
                print(tables_result.stdout)

            # 特定のテーブルの行数を確認
            tables_to_check = ['app_settings', 'prompts', 'summary_usage']
            for table in tables_to_check:
                count_cmd = f'heroku pg:psql --app {{app_name}} -c "SELECT COUNT(*) FROM {{table}};"'
                count_result = subprocess.run(
                    count_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if count_result.returncode == 0:
                    print(f"  {{table}}: {{count_result.stdout.strip()}}")

            return True

        except Exception as e:
            print(f"❌ 確認エラー: {{e}}")
            return False

def main():
    restore = HerokuDumpRestore()

    print("🔄 Heroku Dump 復元ツール")
    print("=" * 40)
    print(f"📁 ダンプファイル: {{restore.dump_file}}")

    # ダンプファイルの存在確認
    if not restore.check_dump_file_exists():
        print("❌ ダンプファイルが見つかりません")
        sys.exit(1)

    # Heroku CLIの確認
    if not restore.check_heroku_cli():
        print("❌ Heroku CLIが必要です")
        sys.exit(1)

    # アプリ名の入力
    app_name = input("\\nHerokuアプリ名を入力してください: ").strip()

    if not app_name:
        print("❌ アプリ名が入力されていません")
        restore.list_apps()
        sys.exit(1)

    # 復元実行
    success = restore.restore_from_dump(app_name)

    if success:
        # 復元後の確認
        verify = input("\\nデータベース状態を確認しますか？ (y/n): ").lower()
        if verify in ['y', 'yes']:
            restore.verify_restore(app_name)

    print("\\n🎯 復元処理完了")

if __name__ == "__main__":
    main()
'''

        restore_file = self.backup_dir / f"restore_script_{self.timestamp}.py"
        with open(restore_file, 'w', encoding='utf-8') as f:
            f.write(restore_script)

        print(f"✅ 復元スクリプト作成: {restore_file}")
        print("💡 使用方法:")
        print(f"   python {restore_file.name}")
        print("   または")
        print(f"   cd {self.backup_dir} && python restore_script_{self.timestamp}.py")

        return restore_file


def create_restore_script_from_backup_data(backup_dir, timestamp):
    """backup_script.pyから呼び出される関数"""
    generator = RestoreScriptGenerator(backup_dir, timestamp)
    return generator.create_restore_script()


def main():
    """スタンドアロン実行用のメイン関数"""
    print("🛠️ Heroku復元スクリプト生成器")
    print("=" * 40)

    # バックアップディレクトリの確認
    default_backup_dir = get_backup_dir()
    backup_dir = input(f"バックアップディレクトリ (デフォルト: {default_backup_dir}): ").strip()
    if not backup_dir:
        backup_dir = default_backup_dir

    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        print(f"❌ ディレクトリが存在しません: {backup_dir}")
        return

    # 利用可能なバックアップファイルを表示
    dump_files = list(backup_dir.glob("heroku_backup_*.dump"))
    if not dump_files:
        print("❌ ダンプファイルが見つかりません")
        return

    print("\\n📁 利用可能なダンプファイル:")
    for i, dump_file in enumerate(dump_files, 1):
        # ファイル名からタイムスタンプを抽出
        timestamp = dump_file.stem.replace("heroku_backup_", "")
        print(f"  {i}. {dump_file.name} ({timestamp})")

    try:
        choice = int(input("\\n復元スクリプトを作成するダンプファイルを選択してください: ")) - 1
        if 0 <= choice < len(dump_files):
            selected_file = dump_files[choice]
            timestamp = selected_file.stem.replace("heroku_backup_", "")

            generator = RestoreScriptGenerator(backup_dir, timestamp)
            restore_file = generator.create_restore_script()

            print(f"\\n🎯 復元スクリプトが正常に作成されました!")
        else:
            print("❌ 無効な選択です")
    except (ValueError, IndexError):
        print("❌ 無効な入力です")


if __name__ == "__main__":
    main()
