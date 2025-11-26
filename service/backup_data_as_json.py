import datetime
import json
from pathlib import Path

from sqlalchemy import create_engine, text


def backup_data_as_json(database_url: str, backup_dir: Path, timestamp: str) -> bool:
    """データをJSON形式でバックアップ"""
    try:
        db_url = database_url
        if "?" in db_url:
            db_url += "&sslmode=require"
        else:
            db_url += "?sslmode=require"

        engine = create_engine(db_url)

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

        backup_file = backup_dir / f"data_backup_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSONバックアップ完了: {backup_file}")
        return True

    except Exception as e:
        print(f"❌ JSONバックアップエラー: {e}")
        return False
