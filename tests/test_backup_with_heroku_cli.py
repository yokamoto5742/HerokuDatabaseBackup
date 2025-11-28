import subprocess
from unittest.mock import Mock, patch

import pytest

from service.backup_with_heroku_cli import backup_with_heroku_cli


class TestBackupWithHerokuCli:
    """backup_with_heroku_cli関数のテスト"""

    @pytest.fixture
    def mock_backup_dir(self, tmp_path):
        """一時的なバックアップディレクトリ"""
        return tmp_path / "backups"

    @pytest.fixture
    def mock_timestamp(self):
        """テスト用タイムスタンプ"""
        return "20231201_120000"

    @pytest.fixture
    def mock_app_name(self):
        """テスト用Herokuアプリ名"""
        return "test-heroku-app"

    def test_backup_with_heroku_cli_success(
        self, mock_backup_dir, mock_timestamp, mock_app_name
    ):
        """正常系: Heroku CLIバックアップが成功する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result) as mock_run:

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            assert result is True
            assert mock_run.call_count == 2

            first_call = mock_run.call_args_list[0]
            assert first_call[0][0] == ["heroku", "pg:backups:capture", "--app", mock_app_name]
            assert first_call[1]['shell'] is True
            assert first_call[1]['check'] is True

            second_call = mock_run.call_args_list[1]
            expected_backup_file = mock_backup_dir / f"heroku_backup_{mock_timestamp}.dump"
            assert second_call[0][0] == [
                "heroku", "pg:backups:download",
                "--app", mock_app_name,
                "--output", str(expected_backup_file)
            ]
            assert second_call[1]['shell'] is True
            assert second_call[1]['capture_output'] is True
            assert second_call[1]['text'] is True

    def test_backup_with_heroku_cli_capture_error(
        self, mock_backup_dir, mock_timestamp, mock_app_name, capsys
    ):
        """異常系: バックアップキャプチャ時にエラーが発生する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_with_heroku_cli.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd')):

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            assert result is False
            captured = capsys.readouterr()
            assert 'Herokuバックアップエラー' in captured.out

    def test_backup_with_heroku_cli_download_failure(
        self, mock_backup_dir, mock_timestamp, mock_app_name, capsys
    ):
        """異常系: バックアップダウンロード時に失敗する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        def run_side_effect(*args, **kwargs):
            if "pg:backups:capture" in args[0]:
                return Mock(returncode=0)
            else:
                result = Mock()
                result.returncode = 1
                result.stderr = "Download failed: Network error"
                return result

        with patch('service.backup_with_heroku_cli.subprocess.run', side_effect=run_side_effect):

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            assert result is False
            captured = capsys.readouterr()
            assert 'Herokuバックアップ失敗' in captured.out
            assert 'Network error' in captured.out

    def test_backup_with_heroku_cli_creates_dump_file_path(
        self, mock_backup_dir, mock_timestamp, mock_app_name
    ):
        """正常系: 正しいファイルパスでdumpファイルが作成される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result) as mock_run:

            backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            download_call = mock_run.call_args_list[1]
            output_path = download_call[0][0][5]
            expected_path = str(mock_backup_dir / f"heroku_backup_{mock_timestamp}.dump")
            assert output_path == expected_path

    def test_backup_with_heroku_cli_logs_info_messages(
        self, mock_backup_dir, mock_timestamp, mock_app_name, capsys
    ):
        """正常系: 適切なログメッセージが出力される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result):

            backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            captured = capsys.readouterr()
            assert 'Herokuバックアップを作成中' in captured.out
            assert 'バックアップをダウンロード中' in captured.out
            assert 'Herokuバックアップ完了' in captured.out

    def test_backup_with_heroku_cli_with_different_app_name(
        self, mock_backup_dir, mock_timestamp
    ):
        """正常系: 異なるアプリ名でも正しく動作する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)
        different_app_name = "different-app-name"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result) as mock_run:

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                different_app_name
            )

            assert result is True
            first_call = mock_run.call_args_list[0]
            assert "--app" in first_call[0][0]
            assert different_app_name in first_call[0][0]

    def test_backup_with_heroku_cli_exception_handling(
        self, mock_backup_dir, mock_timestamp, mock_app_name, capsys
    ):
        """異常系: CalledProcessErrorが発生した場合の処理"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        with patch('service.backup_with_heroku_cli.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd')):

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            assert result is False
            captured = capsys.readouterr()
            assert 'Herokuバックアップエラー' in captured.out

    def test_backup_with_heroku_cli_empty_stderr(
        self, mock_backup_dir, mock_timestamp, mock_app_name
    ):
        """正常系: stderrが空の場合でも正常に完了する"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result):

            result = backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            assert result is True

    def test_backup_with_heroku_cli_shell_parameter(
        self, mock_backup_dir, mock_timestamp, mock_app_name
    ):
        """正常系: subprocess.runがshell=Trueで呼び出される"""
        mock_backup_dir.mkdir(parents=True, exist_ok=True)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch('service.backup_with_heroku_cli.subprocess.run', return_value=mock_result) as mock_run:

            backup_with_heroku_cli(
                mock_backup_dir,
                mock_timestamp,
                mock_app_name
            )

            for call in mock_run.call_args_list:
                assert call[1]['shell'] is True
