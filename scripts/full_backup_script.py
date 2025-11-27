import os

from dotenv import load_dotenv

from service.heroku_login_again import ensure_heroku_login
from service.heroku_postgreSQL_backup import HerokuPostgreSQLBackup


if __name__ == "__main__":
    load_dotenv()

    try:
        backup = HerokuPostgreSQLBackup()

        print("\n💡 利用可能なバックアップ方法:")
        print("1. Heroku CLI バックアップ")
        print("2. JSON データバックアップ")
        print("3. CSV データバックアップ")
        print("4. すべての方法で実行")

        choice = input("\n選択してください (1-4): ").strip()

        # Heroku CLIを使用する選択肢の場合、ログイン状態をチェック
        if choice in ["1", "4"]:
            ensure_heroku_login()

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
