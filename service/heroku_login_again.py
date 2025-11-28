import logging
import os
import subprocess
import threading
import time

from utils.config_manager import load_config

logger = logging.getLogger(__name__)


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
        is_logged_in = result.returncode == 0
        if is_logged_in:
            logger.info("Heroku CLIのログイン状態を確認しました")
        else:
            logger.warning("Heroku CLIのログイン状態が切れています")
        return is_logged_in
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"Herokuログイン状態のチェック中にエラー: {e}")
        return False


def open_folder_async(folder_path: str) -> None:
    """フォルダを非同期で開く"""
    time.sleep(2)
    try:
        if os.path.exists(folder_path):
            subprocess.run(["explorer", folder_path], shell=True)
        else:
            print(f"⚠️ フォルダが見つかりません: {folder_path}")
    except Exception as e:
        print(f"⚠️ フォルダを開く際にエラーが発生: {e}")


def open_folder_in_background(executable_path: str) -> None:
    """フォルダを別スレッドで開く"""
    folder_thread = threading.Thread(target=open_folder_async, args=(executable_path,))
    folder_thread.daemon = True
    folder_thread.start()


def execute_heroku_login() -> bool:
    """Heroku CLIのログインコマンドを実行"""
    logger.info("Heroku CLIでログインを開始します")

    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            ["heroku", "login"],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        time.sleep(1)
        try:
            if process.stdin is not None:
                process.stdin.write("\n")
                process.stdin.flush()
        except (BrokenPipeError, OSError):
            logger.debug("stdinへの書き込みに失敗（プロセス終了済みの可能性）")

        process.communicate(timeout=120)

        if process.returncode == 0:
            logger.info("ログインプロセスが完了しました")
            return True
        else:
            logger.warning("ログインプロセスが終了しました")
            return False

    except subprocess.TimeoutExpired:
        logger.error("ログインがタイムアウトしました")
        if process is not None:
            process.kill()
        return False
    except Exception as e:
        logger.error(f"ログイン処理中にエラーが発生しました: {e}", exc_info=True)
        return False


def prompt_heroku_login() -> None:
    """Herokuに再度ログインするように促す"""
    logger.warning("Heroku CLIのログイン状態が切れています")

    config = load_config()
    executable_file_path = config["Paths"]["executable_file_path"]

    open_folder_in_background(executable_file_path)
    execute_heroku_login()


def ensure_heroku_login() -> bool:
    """Herokuにログインしているかを確認"""
    logger.info("Herokuログイン状態を確認中...")

    if not check_heroku_login():
        prompt_heroku_login()

        # ログイン後に再度チェック
        if not check_heroku_login():
            logger.error("Herokuへのログインに失敗しました")
            return False

        logger.info("Herokuログイン確認完了")
    else:
        logger.info("Herokuログイン確認完了")

    return True
