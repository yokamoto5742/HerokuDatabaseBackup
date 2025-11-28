import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import urlparse

import pytest

from service.heroku_postgreSQL_backup import HerokuPostgreSQLBackup


class TestHerokuPostgreSQLBackup:
    """HerokuPostgreSQLBackupクラスのテスト"""

    @pytest.fixture
    def mock_env_vars(self):
        """モック環境変数"""
        return {
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb"
        }

    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        config = MagicMock()
        config.get.return_value = "C:\\test\\backups"
        return config

    def test_init_success(self, mock_env_vars, mock_config, tmp_path):
        """正常系: 初期化が成功する"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            backup = HerokuPostgreSQLBackup()

            assert backup.database_url == mock_env_vars["DATABASE_URL"]
            assert backup.backup_dir == Path(backup_path)
            assert backup.backup_dir.exists()
            assert backup.timestamp is not None

    def test_init_converts_postgres_to_postgresql(self, mock_config, tmp_path):
        """正常系: postgres://がpostgresql://に変換される"""
        env_vars = {"DATABASE_URL": "postgres://user:pass@localhost:5432/testdb"}
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            backup = HerokuPostgreSQLBackup()

            assert backup.database_url.startswith("postgresql://")
            assert not backup.database_url.startswith("postgres://")

    def test_init_database_url_not_set(self, mock_config):
        """異常系: DATABASE_URLが設定されていない"""
        with patch.dict(os.environ, {}, clear=True), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            with pytest.raises(ValueError, match="DATABASE_URL環境変数が設定されていません"):
                HerokuPostgreSQLBackup()

    def test_init_creates_backup_directory(self, mock_env_vars, mock_config, tmp_path):
        """正常系: バックアップディレクトリが作成される"""
        backup_path = str(tmp_path / "new_backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            backup = HerokuPostgreSQLBackup()

            assert Path(backup_path).exists()
            assert Path(backup_path).is_dir()

    def test_init_parses_url(self, mock_env_vars, mock_config, tmp_path):
        """正常系: データベースURLが正しくパースされる"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            backup = HerokuPostgreSQLBackup()

            assert backup.parsed_url.scheme == "postgresql"
            assert backup.parsed_url.hostname == "localhost"
            assert backup.parsed_url.port == 5432
            assert backup.parsed_url.path == "/testdb"

    def test_backup_with_heroku_cli_method(self, mock_env_vars, mock_config, tmp_path):
        """正常系: backup_with_cliが正しく呼ばれる"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', return_value=True) as mock_cli:

            backup = HerokuPostgreSQLBackup()
            result = backup.backup_with_cli("test-app")

            assert result is True
            mock_cli.assert_called_once_with(backup.backup_dir, backup.timestamp, "test-app")

    def test_backup_data_as_json_method(self, mock_env_vars, mock_config, tmp_path):
        """正常系: backup_as_jsonが正しく呼ばれる"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=True) as mock_json:

            backup = HerokuPostgreSQLBackup()
            result = backup.backup_as_json()

            assert result is True
            mock_json.assert_called_once_with(backup.database_url, backup.backup_dir, backup.timestamp)

    def test_backup_data_as_csv_method(self, mock_env_vars, mock_config, tmp_path):
        """正常系: backup_as_csvが正しく呼ばれる"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=True) as mock_csv:

            backup = HerokuPostgreSQLBackup()
            result = backup.backup_as_csv()

            assert result is True
            mock_csv.assert_called_once_with(backup.database_url, backup.backup_dir, backup.timestamp)

    def test_backup_all_with_app_name(self, mock_env_vars, mock_config, tmp_path, capsys):
        """正常系: backup_all - アプリ名あり、全バックアップ成功"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=True):

            backup = HerokuPostgreSQLBackup()
            results = backup.backup_all(app_name="test-app")

            assert results['heroku_cli'] is True
            assert results['json'] is True
            assert results['csv'] is True

            captured = capsys.readouterr()
            assert 'バックアップ開始' in captured.out
            assert '3/3 の方法で成功' in captured.out

    def test_backup_all_without_app_name(self, mock_env_vars, mock_config, tmp_path, capsys):
        """正常系: backup_all - アプリ名なし、Heroku CLIバックアップをスキップ"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli') as mock_cli, \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=True):

            backup = HerokuPostgreSQLBackup()
            results = backup.backup_all(app_name=None)

            assert results['heroku_cli'] is False
            assert results['json'] is True
            assert results['csv'] is True

            mock_cli.assert_not_called()
            captured = capsys.readouterr()
            assert 'Heroku app名が指定されていないため、Heroku CLIバックアップをスキップ' in captured.out
            assert '2/3 の方法で成功' in captured.out

    def test_backup_all_partial_failure(self, mock_env_vars, mock_config, tmp_path, capsys):
        """正常系: backup_all - 一部のバックアップが失敗"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=False), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=True):

            backup = HerokuPostgreSQLBackup()
            results = backup.backup_all(app_name="test-app")

            assert results['heroku_cli'] is True
            assert results['json'] is False
            assert results['csv'] is True

            captured = capsys.readouterr()
            assert '2/3 の方法で成功' in captured.out

    def test_backup_all_all_failures(self, mock_env_vars, mock_config, tmp_path, capsys):
        """異常系: backup_all - すべてのバックアップが失敗"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', return_value=False), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=False), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=False):

            backup = HerokuPostgreSQLBackup()
            results = backup.backup_all(app_name="test-app")

            assert results['heroku_cli'] is False
            assert results['json'] is False
            assert results['csv'] is False

            captured = capsys.readouterr()
            assert '0/3 の方法で成功' in captured.out

    def test_backup_all_logs_messages(self, mock_env_vars, mock_config, tmp_path, capsys):
        """正常系: backup_all - 適切なログメッセージが出力される"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', return_value=True), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', return_value=True):

            backup = HerokuPostgreSQLBackup()
            backup.backup_all(app_name="test-app")

            captured = capsys.readouterr()
            assert 'バックアップ開始' in captured.out
            assert 'バックアップディレクトリ' in captured.out
            assert 'バックアップ結果' in captured.out
            assert 'heroku_cli' in captured.out
            assert 'json' in captured.out
            assert 'csv' in captured.out

    def test_timestamp_format(self, mock_env_vars, mock_config, tmp_path):
        """正常系: タイムスタンプが正しい形式である"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'):

            backup = HerokuPostgreSQLBackup()

            import re
            timestamp_pattern = r'^\d{8}_\d{6}$'
            assert re.match(timestamp_pattern, backup.timestamp)

    def test_init_loads_dotenv(self, mock_env_vars, mock_config, tmp_path):
        """正常系: .envファイルがロードされる"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv') as mock_load_dotenv:

            HerokuPostgreSQLBackup()

            mock_load_dotenv.assert_called_once()

    def test_backup_all_calls_methods_in_order(self, mock_env_vars, mock_config, tmp_path):
        """正常系: backup_allが正しい順序でメソッドを呼び出す"""
        backup_path = str(tmp_path / "backups")
        mock_config.get.return_value = backup_path
        call_order = []

        def track_cli(*args):
            call_order.append('cli')
            return True

        def track_json(*args):
            call_order.append('json')
            return True

        def track_csv(*args):
            call_order.append('csv')
            return True

        with patch.dict(os.environ, mock_env_vars), \
             patch('service.heroku_postgreSQL_backup.load_config', return_value=mock_config), \
             patch('service.heroku_postgreSQL_backup.load_dotenv'), \
             patch('service.heroku_postgreSQL_backup.backup_with_heroku_cli', side_effect=track_cli), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_json', side_effect=track_json), \
             patch('service.heroku_postgreSQL_backup.backup_data_as_csv', side_effect=track_csv):

            backup = HerokuPostgreSQLBackup()
            backup.backup_all(app_name="test-app")

            assert call_order == ['cli', 'json', 'csv']
