import subprocess
from pathlib import Path


def backup_with_heroku_cli(backup_dir: Path, timestamp: str, app_name: str) -> bool:
    """Heroku CLIを使用してバックアップを作成"""
    try:
        backup_file = backup_dir / f"heroku_backup_{timestamp}.dump"

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
