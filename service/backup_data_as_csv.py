from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from utils.config_manager import get_backup_tables
from utils.database_helper import add_ssl_mode


def backup_data_as_csv(database_url: str, backup_dir: Path, timestamp: str) -> bool:
    """データをCSV形式でバックアップ"""
    try:
        db_url = add_ssl_mode(database_url)

        engine = create_engine(db_url)

        tables = get_backup_tables()
        csv_dir = backup_dir / f"csv_backup_{timestamp}"
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
