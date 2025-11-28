import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytz

from service.cleanup_old_backups import cleanup_old_backups

JST = pytz.timezone('Asia/Tokyo')


class TestCleanupOldBackups:
    """cleanup_old_backups関数のテスト"""

    @pytest.fixture
    def mock_backup_dir(self, tmp_path):
        """一時的なバックアップディレクトリ"""
        return tmp_path / "backups"

    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        config = MagicMock()
        config.getint.return_value = 14
        return config

    def test_cleanup_old_backups_deletes_old_files(self, mock_backup_dir, capsys):
        """正常系: 古いバックアップファイルが削除される"""
        import time

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        old_file = mock_backup_dir / "old_backup.dump"
        recent_file = mock_backup_dir / "recent_backup.dump"
        old_file.touch()
        time.sleep(0.01)
        recent_file.touch()

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=20)
        recent_time = current_time - datetime.timedelta(days=5)

        old_ctime = old_file.stat().st_ctime
        recent_ctime = recent_file.stat().st_ctime

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: old_time if abs(ts - old_ctime) < 0.001 else recent_time

            cleanup_old_backups(mock_backup_dir)

            assert not old_file.exists()
            assert recent_file.exists()

    def test_cleanup_old_backups_with_custom_days(self, mock_backup_dir, capsys):
        """正常系: カスタムの保持期間が指定された場合"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        old_file = mock_backup_dir / "old_backup.dump"
        old_file.touch()

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=8)

        old_ctime = old_file.stat().st_ctime

        with patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: old_time

            cleanup_old_backups(mock_backup_dir, days=7)

            assert not old_file.exists()
            captured = capsys.readouterr()
            assert '1個の古いバックアップファイルを削除しました' in captured.out

    def test_cleanup_old_backups_no_old_files(self, mock_backup_dir, capsys):
        """正常系: 削除対象の古いファイルがない場合"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        recent_file = mock_backup_dir / "recent_backup.dump"
        recent_file.touch()

        current_time = datetime.datetime.now(JST)
        recent_time = current_time - datetime.timedelta(days=5)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: recent_time

            cleanup_old_backups(mock_backup_dir)

            assert recent_file.exists()
            captured = capsys.readouterr()
            assert '削除対象の古いバックアップファイルはありませんでした' in captured.out

    def test_cleanup_old_backups_only_dump_files(self, mock_backup_dir):
        """正常系: .dumpファイルのみが対象となる"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        dump_file = mock_backup_dir / "backup.dump"
        other_file = mock_backup_dir / "backup.json"
        dump_file.touch()
        other_file.touch()

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=20)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: old_time

            cleanup_old_backups(mock_backup_dir)

            assert not dump_file.exists()
            assert other_file.exists()

    def test_cleanup_old_backups_file_deletion_error(self, mock_backup_dir, capsys):
        """異常系: ファイル削除時にエラーが発生した場合"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        old_file = mock_backup_dir / "old_backup.dump"
        old_file.touch()

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=20)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime, \
             patch('pathlib.Path.unlink', side_effect=OSError("Permission denied")):
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: old_time

            cleanup_old_backups(mock_backup_dir)

            captured = capsys.readouterr()
            assert 'ファイル削除エラー' in captured.out
            assert 'Permission denied' in captured.out

    def test_cleanup_old_backups_uses_config_default(self, mock_backup_dir, capsys):
        """正常系: 設定ファイルから保持期間を読み込む"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.cleanup_old_backups.load_config') as mock_config:
            config_mock = MagicMock()
            config_mock.getint.return_value = 30
            mock_config.return_value = config_mock

            cleanup_old_backups(mock_backup_dir)

            mock_config.assert_called_once()
            config_mock.getint.assert_called_once_with('Backup', 'cleanup_days', fallback=30)

    def test_cleanup_old_backups_config_fallback(self, mock_backup_dir, capsys):
        """正常系: 設定が見つからない場合はフォールバック値を使用"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.cleanup_old_backups.load_config') as mock_config:
            config_mock = MagicMock()
            config_mock.getint.side_effect = lambda *args, **kwargs: kwargs.get('fallback')
            mock_config.return_value = config_mock

            cleanup_old_backups(mock_backup_dir)

            config_mock.getint.assert_called_once_with('Backup', 'cleanup_days', fallback=30)

    def test_cleanup_old_backups_exception_handling(self, mock_backup_dir, capsys):
        """異常系: 予期しない例外が発生した場合"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        old_file = mock_backup_dir / "old_backup.dump"
        old_file.touch()

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=20)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = Mock(side_effect=Exception("Unexpected error"))

            cleanup_old_backups(mock_backup_dir)

            captured = capsys.readouterr()
            assert 'バックアップファイル削除エラー' in captured.out

    def test_cleanup_old_backups_multiple_files(self, mock_backup_dir, capsys):
        """正常系: 複数のファイルを削除する"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for i in range(5):
            file = mock_backup_dir / f"old_backup_{i}.dump"
            file.touch()
            files.append(file)

        current_time = datetime.datetime.now(JST)
        old_time = current_time - datetime.timedelta(days=20)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: old_time

            cleanup_old_backups(mock_backup_dir)

            for file in files:
                assert not file.exists()

            captured = capsys.readouterr()
            assert '5個の古いバックアップファイルを削除しました' in captured.out

    def test_cleanup_old_backups_empty_directory(self, mock_backup_dir, capsys):
        """正常系: 空のディレクトリでもエラーが発生しない"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.cleanup_old_backups.load_config') as mock_config:
            config_mock = MagicMock()
            config_mock.getint.return_value = 14
            mock_config.return_value = config_mock

            cleanup_old_backups(mock_backup_dir)

            captured = capsys.readouterr()
            assert '削除対象の古いバックアップファイルはありませんでした' in captured.out

    def test_cleanup_old_backups_boundary_date(self, mock_backup_dir):
        """正常系: 境界日のファイルは削除されない"""

        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        boundary_file = mock_backup_dir / "boundary_backup.dump"
        boundary_file.touch()

        current_time = datetime.datetime.now(JST)
        boundary_time = current_time - datetime.timedelta(days=14)

        with patch('service.cleanup_old_backups.load_config') as mock_config, \
             patch('service.cleanup_old_backups.datetime') as mock_datetime:
            mock_config.return_value.getint.return_value = 14
            mock_datetime.datetime.now.return_value = current_time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.datetime.fromtimestamp = lambda ts, tz: boundary_time

            cleanup_old_backups(mock_backup_dir)

            assert boundary_file.exists()
