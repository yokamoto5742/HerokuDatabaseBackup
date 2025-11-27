import os
import subprocess
import sys
import webbrowser

from utils.config_manager import load_config


def check_heroku_login() -> bool:
    """Heroku CLIのログイン状態をチェック"""
    try:
        result = subprocess.run(
            ["heroku", "auth:whoami"],
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def prompt_heroku_login() -> None:
    """Herokuに再度ログインするように促す"""
    print("\n⚠️ Heroku CLIのログイン状態が切れています")
    print("⚠️ Herokuに再度ログインしてください\n")

    try:
        # Heroku CLIでログインコマンドを実行
        print("🔄 Heroku CLIでログインを開始...")
        subprocess.run(["heroku", "login"], shell=True)

        # executable_file_pathのフォルダを開く
        config = load_config()
        executable_file_path = config["Paths"]["executable_file_path"]

        if os.path.exists(executable_file_path):
            print(f"📂 フォルダを開いています: {executable_file_path}")
            if sys.platform == "win32":
                os.startfile(executable_file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", executable_file_path])
            else:
                subprocess.run(["xdg-open", executable_file_path])
        else:
            print(f"⚠️ フォルダが見つかりません: {executable_file_path}")

    except Exception as e:
        print(f"❌ ログイン処理中にエラーが発生しました: {e}")


def ensure_heroku_login() -> bool:
    """Herokuにログインしているか確認し、必要に応じてログインを促す"""
    if not check_heroku_login():
        prompt_heroku_login()

        # ログイン後に再度チェック
        if not check_heroku_login():
            print("❌ Herokuへのログインに失敗しました")
            return False

    return True
