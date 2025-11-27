import configparser
import os
import sys


def _get_config_path() -> str:
    """内部使用のみ"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'config.ini')


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config_path = _get_config_path()
    try:
        with open(config_path, encoding='utf-8') as f:
            config.read_file(f)
    except FileNotFoundError:
        print(f"設定ファイルが見つかりません: {config_path}")
        raise
    except PermissionError:
        print(f"設定ファイルを読み取る権限がありません: {config_path}")
        raise
    except configparser.Error as e:
        print(f"設定ファイルの解析中にエラーが発生しました: {e}")
        raise
    return config


def save_config(config: configparser.ConfigParser) -> None:
    config_path = _get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except PermissionError:
        print(f"設定ファイルを書き込む権限がありません: {config_path}")
        raise
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise


def get_log_directory() -> str:
    config = load_config()
    return config.get('LOGGING', 'log_directory', fallback='logs')


def get_log_retention_days() -> int:
    config = load_config()
    return config.getint('LOGGING', 'log_retention_days', fallback=7)


def get_log_level() -> str:
    config = load_config()
    return config.get('LOGGING', 'log_level', fallback='INFO').upper()


def get_backup_tables() -> list[str]:
    """バックアップ対象のテーブル名リストを取得"""
    config = load_config()
    tables_str = config.get('Database', 'backup_tables', fallback='app_settings,prompts,summary_usage')
    return [table.strip() for table in tables_str.split(',')]
