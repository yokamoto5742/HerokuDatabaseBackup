from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from service.backup_data_as_csv import backup_data_as_csv


class TestBackupDataAsCsv:
    """backup_data_as_csv関数のテスト"""

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
    def mock_dataframe(self):
        """モックDataFrame"""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['test1', 'test2', 'test3'],
            'value': [100, 200, 300]
        })

    def test_backup_data_as_csv_success(
        self, mock_database_url, mock_backup_dir, mock_timestamp, mock_dataframe
    ):
        """正常系: CSVバックアップが成功する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine') as mock_engine, \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=mock_dataframe):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            csv_dir = mock_backup_dir / f"csv_backup_{mock_timestamp}"
            assert csv_dir.exists()
            assert csv_dir.is_dir()

            for table in ['app_settings', 'prompts', 'summary_usage']:
                csv_file = csv_dir / f"{table}.csv"
                assert csv_file.exists()
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                assert len(df) == 3

    def test_backup_data_as_csv_appends_sslmode_without_query_params(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: クエリパラメータなしの場合にsslmodeが追加される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine') as mock_engine, \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=pd.DataFrame()):

            backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            called_url = mock_engine.call_args[0][0]
            assert '?sslmode=require' in called_url

    def test_backup_data_as_csv_appends_sslmode_with_query_params(
        self, mock_backup_dir, mock_timestamp
    ):
        """正常系: クエリパラメータありの場合にsslmodeが追加される"""
        database_url = "postgresql://user:pass@localhost:5432/testdb?connect_timeout=10"
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine') as mock_engine, \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=pd.DataFrame()):

            backup_data_as_csv(
                database_url,
                mock_backup_dir,
                mock_timestamp
            )

            called_url = mock_engine.call_args[0][0]
            assert '&sslmode=require' in called_url

    def test_backup_data_as_csv_creates_directory(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: CSVバックアップディレクトリが作成される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine'), \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=pd.DataFrame()):

            backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            csv_dir = mock_backup_dir / f"csv_backup_{mock_timestamp}"
            assert csv_dir.exists()
            assert csv_dir.is_dir()

    def test_backup_data_as_csv_handles_table_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp, mock_dataframe, capsys
    ):
        """正常系: 一部のテーブルでエラーが発生してもバックアップは続行される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        def read_sql_side_effect(table, engine):
            if table == 'prompts':
                raise Exception("Table does not exist")
            return mock_dataframe

        with patch('service.backup_data_as_csv.create_engine'), \
             patch('service.backup_data_as_csv.pd.read_sql_table', side_effect=read_sql_side_effect):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            captured = capsys.readouterr()
            assert 'prompts' in captured.out
            assert 'Table does not exist' in captured.out

    def test_backup_data_as_csv_connection_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp, capsys
    ):
        """異常系: データベース接続エラーが発生した場合"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine', side_effect=Exception("Connection failed")):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is False
            captured = capsys.readouterr()
            assert 'CSVバックアップエラー' in captured.out
            assert 'Connection failed' in captured.out

    def test_backup_data_as_csv_empty_dataframe(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """正常系: 空のDataFrameでもバックアップが成功する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)
        empty_df = pd.DataFrame()

        with patch('service.backup_data_as_csv.create_engine'), \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=empty_df):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            csv_dir = mock_backup_dir / f"csv_backup_{mock_timestamp}"
            assert csv_dir.exists()

            for table in ['app_settings', 'prompts', 'summary_usage']:
                csv_file = csv_dir / f"{table}.csv"
                assert csv_file.exists()

    def test_backup_data_as_csv_directory_creation_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp
    ):
        """異常系: ディレクトリ作成エラーが発生した場合"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine'), \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=pd.DataFrame()), \
             patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is False

    def test_backup_data_as_csv_file_write_error(
        self, mock_database_url, mock_backup_dir, mock_timestamp, mock_dataframe, capsys
    ):
        """異常系: ファイル書き込みエラーが発生してもバックアップ処理は続行される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine'), \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=mock_dataframe), \
             patch.object(pd.DataFrame, 'to_csv', side_effect=OSError("Disk full")):

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            captured = capsys.readouterr()
            assert 'Disk full' in captured.out

    def test_backup_data_as_csv_all_tables_exported(
        self, mock_database_url, mock_backup_dir, mock_timestamp, mock_dataframe
    ):
        """正常系: すべてのテーブルがエクスポートされる"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_data_as_csv.create_engine') as mock_engine, \
             patch('service.backup_data_as_csv.pd.read_sql_table', return_value=mock_dataframe) as mock_read:

            result = backup_data_as_csv(
                mock_database_url,
                mock_backup_dir,
                mock_timestamp
            )

            assert result is True
            assert mock_read.call_count == 3
            tables_called = [call[0][0] for call in mock_read.call_args_list]
            assert 'app_settings' in tables_called
            assert 'prompts' in tables_called
            assert 'summary_usage' in tables_called
