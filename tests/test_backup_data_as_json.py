import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from service.backup_data_as_json import backup_data_as_json


class TestBackupDataAsJson:
    """backup_data_as_json関数のテスト"""

    @pytest.fixture
    def mock_database_url(self):
        """モックデータベースURL"""
        return "postgresql://user:pass@localhost:5432/testdb"

    @pytest.fixture
    def mock_backup_dir(self, tmp_path):
        """一時的なバックアップディレクトリ"""
        return tmp_path / "backups"

    @pytest.fixture
    def mock_timestamp(self):
        """テスト用タイムスタンプ"""
        return "20231201_120000"

    @pytest.fixture
    def mock_row_data(self):
        """モックデータベース行データ"""
        row1 = Mock()
        row1._mapping = {
            'id': 1,
            'name': 'test_data',
            'created_at': datetime.datetime(2023, 12, 1, 12, 0, 0)
        }
        row2 = Mock()
        row2._mapping = {
            'id': 2,
            'name': 'test_data2',
            'created_at': datetime.datetime(2023, 12, 2, 12, 0, 0)
        }
        return [row1, row2]

    def test_backup_data_as_json_success(
        self, mock_database_url, mock_backup_dir, mock_timestamp, mock_row_data
    ):
        """正常系: JSONバックアップが成功する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter(mock_row_data))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            result = backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            backup_file = mock_backup_dir / f"data_backup_{mock_timestamp}.json"
            assert backup_file.exists()

            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert 'app_settings' in data
            assert 'prompts' in data
            assert 'summary_usage' in data
            assert len(data['app_settings']) == 2
            assert data['app_settings'][0]['id'] == 1
            assert data['app_settings'][0]['created_at'] == '2023-12-01T12:00:00'

    def test_backup_data_as_json_appends_sslmode_without_query_params(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: クエリパラメータなしの場合にsslmodeが追加される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([]))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            called_url = mock_engine.call_args[0][0]
            assert '?sslmode=require' in called_url

    def test_backup_data_as_json_appends_sslmode_with_query_params(
        self, mock_backup_dir, mock_timestamp
    ):
        """正常系: クエリパラメータありの場合にsslmodeが追加される"""
        database_url = "postgresql://user:pass@localhost:5432/testdb?connect_timeout=10"
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([]))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            backup_data_as_json(
                database_url,
                mock_backup_dir,
                mock_timestamp
            )

            called_url = mock_engine.call_args[0][0]
            assert '&sslmode=require' in called_url

    def test_backup_data_as_json_handles_table_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp, capsys
    ):
        """正常系: 一部のテーブルでエラーが発生してもバックアップは続行される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()

            def execute_side_effect(query):
                query_str = str(query)
                if 'prompts' in query_str:
                    raise Exception("Table does not exist")
                mock_result = MagicMock()
                mock_result.__iter__ = Mock(return_value=iter([]))
                return mock_result

            mock_conn.execute.side_effect = execute_side_effect
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            result = backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            captured = capsys.readouterr()
            assert 'prompts' in captured.out
            assert 'Table does not exist' in captured.out

    def test_backup_data_as_json_handles_datetime_serialization(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: datetimeオブジェクトがISO形式に変換される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_row = Mock()
        mock_row._mapping = {
            'id': 1,
            'created_at': datetime.datetime(2023, 12, 1, 12, 0, 0),
            'updated_at': datetime.datetime(2023, 12, 2, 13, 30, 45)
        }

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([mock_row]))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            result = backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            backup_file = mock_backup_dir / f"data_backup_{mock_timestamp}.json"
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data['app_settings'][0]['created_at'] == '2023-12-01T12:00:00'
            assert data['app_settings'][0]['updated_at'] == '2023-12-02T13:30:45'

    def test_backup_data_as_json_connection_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp, capsys
    ):
        """異常系: データベース接続エラーが発生した場合"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")

            result = backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is False
            captured = capsys.readouterr()
            assert 'JSONバックアップエラー' in captured.out
            assert 'Connection failed' in captured.out

    def test_backup_data_as_json_write_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """異常系: ファイル書き込みエラーが発生した場合"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([]))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            with patch('builtins.open', side_effect=OSError("Permission denied")):
                result = backup_data_as_json(
                    mock_database_url,
                    mock_backup_dir,
                    mock_timestamp
                )

                assert result is False

    def test_backup_data_as_json_empty_tables(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: 空のテーブルでもバックアップが成功する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_json.create_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = Mock(return_value=iter([]))
            mock_conn.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            result = backup_data_as_json(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            backup_file = mock_backup_dir / f"data_backup_{mock_timestamp}.json"
            assert backup_file.exists()

            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data['app_settings'] == []
            assert data['prompts'] == []
            assert data['summary_usage'] == []
