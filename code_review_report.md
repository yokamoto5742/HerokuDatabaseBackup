# コードレビューレポート


## 重大な問題 (High Priority)

### 1. コードの重複 - データベースURL処理

**問題箇所**:
- `service/backup_data_as_json.py:11-15`
- `service/backup_data_as_csv.py:10-14`

**内容**:
```python
db_url = database_url
if "?" in db_url:
    db_url += "&sslmode=require"
else:
    db_url += "?sslmode=require"
```

このロジックが2つのファイルで完全に重複しています。

**推奨対応**:
共通のヘルパー関数を作成して重複を排除:
```python
# utils/database_helper.py
def add_ssl_mode(database_url: str) -> str:
    """データベースURLにSSLモードを追加"""
    separator = "&" if "?" in database_url else "?"
    return f"{database_url}{separator}sslmode=require"
```

**理由**: DRY原則に違反。変更時に複数箇所の修正が必要で、バグの温床となる。

---

### 2. テーブル名のハードコーディング

**問題箇所**:
- `service/backup_data_as_json.py:20`
- `service/backup_data_as_csv.py:18`
- `scripts/create_restore_script.py:153`

**内容**:
```python
tables = ['app_settings', 'prompts', 'summary_usage']
```

3箇所でテーブル名がハードコーディングされています。

**推奨対応**:
設定ファイルで一元管理:
```python
# utils/config.ini
[Database]
BACKUP_TABLES = ['app_settings', 'prompts', 'summary_usage']
```

**理由**: テーブルの追加・削除時に複数箇所を修正する必要がある。保守性が低い。

---

### 3. 長すぎる関数

**問題箇所**: `service/heroku_login_again.py:52-109`

**内容**:
`prompt_heroku_login()` 関数が58行もあり、複数の責任を持っています。

**推奨対応**:
関数を複数の小さな関数に分割:
```python
def open_folder_in_background(executable_path: str) -> None:
    """フォルダを別スレッドで開く"""
    folder_thread = threading.Thread(
        target=open_folder_async,
        args=(executable_path,)
    )
    folder_thread.daemon = True
    folder_thread.start()

def execute_heroku_login() -> bool:
    """Heroku CLIログインコマンドを実行"""
    # ログイン処理のみに集中
    ...

def prompt_heroku_login() -> None:
    """Herokuに再度ログインするように促す（オーケストレーター）"""
    # 各ヘルパー関数を呼び出すだけ
    ...
```

**理由**: 単一責任の原則（SRP）に違反。テストが困難で、可読性も低い。関数は50行以下が理想。

---

## 中程度の問題 (Medium Priority)

### 4. ベア except の使用

**問題箇所**: `service/heroku_login_again.py:88-89`

**内容**:
```python
try:
    if process.stdin is not None:
        process.stdin.write("\n")
        process.stdin.flush()
except:
    pass
```

**推奨対応**:
具体的な例外を捕捉:
```python
except (BrokenPipeError, OSError):
    logger.debug("stdin への書き込みに失敗（プロセス終了済みの可能性）")
```

**理由**: すべての例外を無視するのは危険。予期しないバグを見逃す可能性がある。

---

### 5. 冗長なメソッド名

**問題箇所**: `service/heroku_postgreSQL_backup.py:42-50`

**内容**:
```python
def backup_with_heroku_cli_method(self, app_name: str) -> bool:
    return backup_with_heroku_cli(self.backup_dir, self.timestamp, app_name)

def backup_data_as_json_method(self) -> bool:
    return backup_data_as_json(self.database_url, self.backup_dir, self.timestamp)

def backup_data_as_csv_method(self) -> bool:
    return backup_data_as_csv(self.database_url, self.backup_dir, self.timestamp)
```

**推奨対応**:
メソッド名を簡潔に:
```python
def backup_with_cli(self, app_name: str) -> bool:
    ...

def backup_as_json(self) -> bool:
    ...

def backup_as_csv(self) -> bool:
    ...
```

**理由**: `_method` サフィックスは不要。クラスのメソッドであることは自明。

---

### 6. グローバル変数の使用

**問題箇所**: `utils/config_manager.py:16`

**内容**:
```python
CONFIG_PATH = get_config_path()
```

**推奨対応**:
関数呼び出し時に毎回取得するか、プライベート変数として扱う:
```python
def _get_config_path() -> str:
    """内部使用のみ"""
    ...

def load_config() -> configparser.ConfigParser:
    config_path = _get_config_path()
    ...
```

**理由**: グローバル変数はテストを困難にし、予期しない副作用を生む可能性がある。

---



## 軽微な問題 (Low Priority)

### 8. ログ出力とprint文の混在

**問題箇所**: 複数ファイル（例: `service/cleanup_old_backups.py`）

**内容**:
```python
logger.info(f"古いバックアップファイルを削除: {backup_file.name}")
print(f"🗑️  古いバックアップファイルを削除: {backup_file.name}")
```

**推奨対応**:
ログ出力に一本化し、ユーザー向け出力が必要な場合はカスタムハンドラーを使用:
```python
# カスタムログハンドラーでコンソール出力を制御
logger.info(f"古いバックアップファイルを削除: {backup_file.name}")
```

### 10. 型ヒントの不足

**問題箇所**: `scripts/create_restore_script.py:15-17`

**内容**:
```python
def get_backup_dir():
    config = load_config()
    return config.get('Paths', 'backup_path')
```

**推奨対応**:
```python
def get_backup_dir() -> str:
    config = load_config()
    return config.get('Paths', 'backup_path')
```

**理由**: 型ヒントはコードの可読性を向上させ、IDE のサポートを強化する。

---

### 11. import文の順序

**問題箇所**: `service/heroku_postgreSQL_backup.py:1-13`

**内容**:
```python
import datetime
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from service.backup_data_as_csv import backup_data_as_csv
from service.backup_data_as_json import backup_data_as_json
from service.backup_with_heroku_cli import backup_with_heroku_cli
from utils.config_manager import load_config
```

**評価**: 概ね良好ですが、`from pathlib import Path` と `from urllib.parse import urlparse` の順序が逆。

**推奨対応**:
アルファベット順に並べる:
```python
import datetime
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

from service.backup_data_as_csv import backup_data_as_csv
...
```

**理由**: CLAUDE.md の指示に従う。一貫性のある順序はメンテナンス性を向上させる。

---

### 12. 不要な空行

**問題箇所**: `utils/config_manager.py:17-18`

**内容**:
```python
CONFIG_PATH = get_config_path()



def load_config() -> configparser.ConfigParser:
```

2行の空行は1行にすべき。

**推奨対応**:
PEP8に従い、トップレベル関数の間は2行空ける:
```python
CONFIG_PATH = get_config_path()


def load_config() -> configparser.ConfigParser:
```
