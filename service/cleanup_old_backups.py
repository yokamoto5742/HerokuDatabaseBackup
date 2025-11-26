import datetime
from pathlib import Path

import pytz

from config_manager import load_config

JST = pytz.timezone('Asia/Tokyo')


def cleanup_old_backups(backup_dir: Path, days: int | None = None) -> None:
    """古いバックアップファイルを削除"""
    if days is None:
        config = load_config()
        days = config.getint('Backup', 'cleanup_days', fallback=30)
    try:
        current_time = datetime.datetime.now(JST)
        cutoff_time = current_time - datetime.timedelta(days=days)

        deleted_count = 0
        for backup_file in backup_dir.glob("*.dump"):
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
