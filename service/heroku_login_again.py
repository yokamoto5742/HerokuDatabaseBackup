import os
import subprocess
import sys
import threading
import time

from utils.config_manager import load_config


def check_heroku_login() -> bool:
    """Heroku CLIのログイン状態をチェック"""
    try:
        result = subprocess.run(
            ["heroku", "auth:whoami"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def open_folder_async(folder_path: str) -> None:
    """フォルダを非同期で開く"""
    time.sleep(2)
    try:
        if os.path.exists(folder_path):
            print(f"📂 フォルダを開いています: {folder_path}")
            if sys.platform == "win32":
                subprocess.run(["explorer", folder_path], shell=True)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
        else:
            print(f"⚠️ フォルダが見つかりません: {folder_path}")
    except Exception as e:
        print(f"⚠️ フォルダを開く際にエラーが発生: {e}")


def prompt_heroku_login() -> None:
    """Herokuに再度ログインするように促す"""
    print("\n⚠️ Heroku CLIのログイン状態が切れています")
    print("⚠️ Herokuに再度ログインしてください\n")

    try:
        config = load_config()
        executable_file_path = config["Paths"]["executable_file_path"]

        # フォルダを非同期で開く（ログインプロセスをブロックしないように）
        folder_thread = threading.Thread(target=open_folder_async, args=(executable_file_path,))
        folder_thread.daemon = True
        folder_thread.start()

        # Heroku CLIでログインコマンドを実行（自動的にEnterを送信）
        print("🔄 Heroku CLIでログインを開始...")
        print("💡 ブラウザが開いたらログインしてください")

        process = subprocess.Popen(
            ["heroku", "login"],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 少し待ってからEnterキーを自動送信
        time.sleep(1)
        try:
            process.stdin.write("\n")
            process.stdin.flush()
        except:
            pass

        # ログインプロセスの完了を待つ
        stdout, stderr = process.communicate(timeout=120)

        if process.returncode == 0:
            print("✅ ログインプロセスが完了しました")
        else:
            print(f"⚠️ ログインプロセスが終了しました: {stderr}")

    except subprocess.TimeoutExpired:
        print("⚠️ ログインがタイムアウトしました")
        process.kill()
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

        print("✅ Herokuログイン確認完了")

    return True
