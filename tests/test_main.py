# -*- coding: utf-8 -*-
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestMain:
    """main.pyのエントリーポイントテスト"""

    @pytest.fixture
    def mock_env_vars(self):
        """テスト用環境変数"""
        return {
            "HEROKU_APP_NAME": "test-heroku-app",
            "DATABASE_URL": "postgresql://test:test@localhost/testdb"
        }

    @pytest.fixture
    def mock_backup_instance(self):
        """モックバックアップインスタンス"""
        mock_backup = Mock()
        mock_backup.backup_dir = Path("C:\\test\\backups")
        mock_backup.timestamp = "20231201_120000"
        return mock_backup

    def test_main_success_all_functions_called_correctly(
        self, mock_env_vars, mock_backup_instance, caplog, monkeypatch
    ):
        """正常系: 全ての処理が正常に完了し、関数が正しい順序で呼ばれる"""
        caplog.set_level(logging.INFO)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('dotenv.load_dotenv') as mock_load_dotenv, \
             patch('utils.config_manager.get_log_directory', return_value=Path("C:\\test\\logs")) as mock_get_log_dir, \
             patch('utils.config_manager.get_log_retention_days', return_value=14) as mock_get_retention, \
             patch('utils.log_rotation.setup_logging') as mock_setup_logging, \
             patch('service.heroku_login_again.ensure_heroku_login', return_value=True) as mock_ensure_login, \
             patch('service.heroku_postgreSQL_backup.HerokuPostgreSQLBackup', return_value=mock_backup_instance) as mock_backup_class, \
             patch('service.cleanup_old_backups.cleanup_old_backups') as mock_cleanup, \
             patch('service.backup_with_heroku_cli.backup_with_heroku_cli', return_value=True) as mock_backup_cli:

            import runpy
            runpy.run_path('main.py', run_name='__main__')

            mock_load_dotenv.assert_called_once()
            mock_get_log_dir.assert_called_once()
            mock_get_retention.assert_called_once()
            mock_setup_logging.assert_called_once_with(
                log_directory=Path("C:\\test\\logs"),
                log_retention_days=14
            )
            mock_ensure_login.assert_called_once()
            mock_backup_class.assert_called_once()
            mock_cleanup.assert_called_once_with(mock_backup_instance.backup_dir)
            mock_backup_cli.assert_called_once_with(
                mock_backup_instance.backup_dir,
                mock_backup_instance.timestamp,
                "test-heroku-app"
            )

            assert 'バックアップ処理を開始します' in caplog.text
            assert 'Herokuアプリ: test-heroku-app' in caplog.text
            assert 'バックアップ処理が正常に完了しました' in caplog.text

    def test_main_functions_called_in_correct_order(
        self, mock_env_vars, mock_backup_instance, monkeypatch
    ):
        """正常系: 関数が正しい順序で呼び出される"""
        call_order = []

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        def track_call(name):
            def wrapper(*args, **kwargs):
                call_order.append(name)
                if name == 'HerokuPostgreSQLBackup':
                    return mock_backup_instance
                return Mock()
            return wrapper

        with patch('main.load_dotenv', side_effect=track_call('load_dotenv')), \
             patch('main.get_log_directory', side_effect=track_call('get_log_directory')), \
             patch('main.get_log_retention_days', side_effect=track_call('get_log_retention_days')), \
             patch('main.setup_logging', side_effect=track_call('setup_logging')), \
             patch('main.ensure_heroku_login', side_effect=track_call('ensure_heroku_login')), \
             patch('main.HerokuPostgreSQLBackup', side_effect=track_call('HerokuPostgreSQLBackup')), \
             patch('main.cleanup_old_backups', side_effect=track_call('cleanup_old_backups')), \
             patch('main.backup_with_heroku_cli', side_effect=track_call('backup_with_heroku_cli')):

            import runpy
            runpy.run_module('main', run_name='__main__')

            expected_order = [
                'load_dotenv',
                'get_log_directory',
                'get_log_retention_days',
                'setup_logging',
                'ensure_heroku_login',
                'HerokuPostgreSQLBackup',
                'cleanup_old_backups',
                'backup_with_heroku_cli'
            ]
            assert call_order == expected_order

    def test_main_environment_variable_loaded_correctly(
        self, mock_env_vars, mock_backup_instance, caplog, monkeypatch
    ):
        """正常系: 環境変数が正しく読み込まれる"""
        caplog.set_level(logging.INFO)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', return_value=True) as mock_backup_cli:

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'Herokuアプリ: test-heroku-app' in caplog.text
            mock_backup_cli.assert_called_once_with(
                mock_backup_instance.backup_dir,
                mock_backup_instance.timestamp,
                "test-heroku-app"
            )

    def test_main_exception_handling_logs_error(
        self, mock_env_vars, caplog, capsys, monkeypatch
    ):
        """異常系: 例外が発生した場合のエラーハンドリング"""
        caplog.set_level(logging.ERROR)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', side_effect=Exception("Login failed")):

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'エラーが発生しました: Login failed' in caplog.text

            captured = capsys.readouterr()
            assert '❌ エラー: Login failed' in captured.out

    def test_main_exception_during_backup_cleanup(
        self, mock_env_vars, mock_backup_instance, caplog, monkeypatch
    ):
        """異常系: cleanup_old_backups実行中に例外が発生"""
        caplog.set_level(logging.ERROR)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups', side_effect=Exception("Cleanup error")):

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'エラーが発生しました: Cleanup error' in caplog.text

    def test_main_exception_during_heroku_cli_backup(
        self, mock_env_vars, mock_backup_instance, caplog, monkeypatch
    ):
        """異常系: backup_with_heroku_cli実行中に例外が発生"""
        caplog.set_level(logging.ERROR)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', side_effect=Exception("Backup failed")):

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'エラーが発生しました: Backup failed' in caplog.text

    def test_main_log_messages_output_correctly(
        self, mock_env_vars, mock_backup_instance, caplog, monkeypatch
    ):
        """正常系: ログメッセージが正しく出力される"""
        caplog.set_level(logging.INFO)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', return_value=True):

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'バックアップ処理を開始します' in caplog.text
            assert 'Herokuアプリ: test-heroku-app' in caplog.text
            assert 'バックアップ処理が正常に完了しました' in caplog.text

    def test_main_with_none_app_name(
        self, mock_backup_instance, caplog, monkeypatch
    ):
        """正常系: HEROKU_APP_NAMEがNoneの場合でも処理が継続される"""
        caplog.set_level(logging.INFO)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', return_value=True) as mock_backup_cli:

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'Herokuアプリ: None' in caplog.text
            mock_backup_cli.assert_called_once_with(
                mock_backup_instance.backup_dir,
                mock_backup_instance.timestamp,
                None
            )

    def test_main_exception_includes_traceback(
        self, mock_env_vars, caplog, monkeypatch
    ):
        """異常系: 例外発生時にトレースバック情報が含まれる"""
        caplog.set_level(logging.ERROR)

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', side_effect=RuntimeError("Test error")):

            import runpy
            runpy.run_module('main', run_name='__main__')

            assert 'エラーが発生しました: Test error' in caplog.text

            error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
            assert len(error_records) > 0
            assert error_records[0].exc_info is not None

    def test_main_backup_instance_created_correctly(
        self, mock_env_vars, mock_backup_instance, monkeypatch
    ):
        """正常系: HerokuPostgreSQLBackupインスタンスが正しく作成される"""
        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=Path("C:\\test\\logs")), \
             patch('main.get_log_retention_days', return_value=14), \
             patch('main.setup_logging'), \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance) as mock_backup_class, \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', return_value=True):

            import runpy
            runpy.run_module('main', run_name='__main__')

            mock_backup_class.assert_called_once_with()

    def test_main_logging_setup_with_correct_parameters(
        self, mock_env_vars, mock_backup_instance, monkeypatch
    ):
        """正常系: ロギングが正しいパラメータで設定される"""
        test_log_dir = Path("C:\\custom\\logs")
        test_retention = 30

        for key, value in mock_env_vars.items():
            monkeypatch.setenv(key, value)

        with patch('main.load_dotenv'), \
             patch('main.get_log_directory', return_value=test_log_dir) as mock_get_log_dir, \
             patch('main.get_log_retention_days', return_value=test_retention) as mock_get_retention, \
             patch('main.setup_logging') as mock_setup_logging, \
             patch('main.ensure_heroku_login', return_value=True), \
             patch('main.HerokuPostgreSQLBackup', return_value=mock_backup_instance), \
             patch('main.cleanup_old_backups'), \
             patch('main.backup_with_heroku_cli', return_value=True):

            import runpy
            runpy.run_module('main', run_name='__main__')

            mock_get_log_dir.assert_called_once()
            mock_get_retention.assert_called_once()
            mock_setup_logging.assert_called_once_with(
                log_directory=test_log_dir,
                log_retention_days=test_retention
            )
