import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def backup_with_heroku_cli(backup_dir: Path, timestamp: str, app_name: str) -> bool:
    """Heroku CLIを使用してバックアップを作成"""
    try:
        backup_file = backup_dir / f"heroku_backup_{timestamp}.dump"

        logger.info("Herokuバックアップを作成中...")
        print("🔄 Herokuバックアップを作成中...")
        subprocess.run([
            "heroku", "pg:backups:capture",
            "--app", app_name
        ], shell=True, check=True)

        logger.info("バックアップをダウンロード中...")
        print("🔄 バックアップをダウンロード中...")
        result = subprocess.run([
            "heroku", "pg:backups:download",
            "--app", app_name,
            "--output", str(backup_file)
        ], shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Herokuバックアップ完了: {backup_file}")
            print(f"✅ Herokuバックアップ完了: {backup_file}")
            return True
        else:
            logger.error(f"Herokuバックアップ失敗: {result.stderr}")
            print(f"❌ Herokuバックアップ失敗: {result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Herokuバックアップエラー: {e}", exc_info=True)
        print(f"❌ Herokuバックアップエラー: {e}")
        return False
