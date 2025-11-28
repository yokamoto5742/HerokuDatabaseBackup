import subprocess
from unittest.mock import Mock, patch

import pytest

from service.heroku_login_again import (
    check_heroku_login,
    ensure_heroku_login,
    open_folder_async,
    prompt_heroku_login,
)


class TestCheckHerokuLogin:
    """check_heroku_login関数のテスト"""

    def test_check_heroku_login_success(self):
        """正常系: Heroku CLIログイン成功"""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch('service.heroku_login_again.subprocess.run', return_value=mock_result) as mock_run:
            result = check_heroku_login()

            assert result is True
            mock_run.assert_called_once_with(
                ["heroku", "auth:whoami"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

    def test_check_heroku_login_not_logged_in(self):
        """異常系: Heroku CLIにログインしていない"""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch('service.heroku_login_again.subprocess.run', return_value=mock_result):
            result = check_heroku_login()

            assert result is False

    def test_check_heroku_login_timeout(self):
        """異常系: タイムアウトが発生"""
        with patch('service.heroku_login_again.subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 10)):
            result = check_heroku_login()

            assert result is False

    def test_check_heroku_login_called_process_error(self):
        """異常系: CalledProcessErrorが発生"""
        with patch('service.heroku_login_again.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd')):
            result = check_heroku_login()

            assert result is False


class TestOpenFolderAsync:
    """open_folder_async関数のテスト"""

    def test_open_folder_async_windows(self, tmp_path, capsys):
        """正常系: Windows環境でフォルダを開く"""
        folder_path = str(tmp_path)

        with patch('service.heroku_login_again.time.sleep'), \
             patch('service.heroku_login_again.sys.platform', 'win32'), \
             patch('service.heroku_login_again.subprocess.run') as mock_run:

            open_folder_async(folder_path)

            mock_run.assert_called_once_with(["explorer", folder_path], shell=True)
            captured = capsys.readouterr()
            assert 'フォルダを開いています' in captured.out

    def test_open_folder_async_macos(self, tmp_path, capsys):
        """正常系: macOS環境でフォルダを開く"""
        folder_path = str(tmp_path)

        with patch('service.heroku_login_again.time.sleep'), \
             patch('service.heroku_login_again.sys.platform', 'darwin'), \
             patch('service.heroku_login_again.subprocess.run') as mock_run:

            open_folder_async(folder_path)

            mock_run.assert_called_once_with(["open", folder_path])

    def test_open_folder_async_linux(self, tmp_path, capsys):
        """正常系: Linux環境でフォルダを開く"""
        folder_path = str(tmp_path)

        with patch('service.heroku_login_again.time.sleep'), \
             patch('service.heroku_login_again.sys.platform', 'linux'), \
             patch('service.heroku_login_again.subprocess.run') as mock_run:

            open_folder_async(folder_path)

            mock_run.assert_called_once_with(["xdg-open", folder_path])

    def test_open_folder_async_folder_not_exists(self, capsys):
        """異常系: フォルダが存在しない"""
        non_existent_path = "/non/existent/path"

        with patch('service.heroku_login_again.time.sleep'):
            open_folder_async(non_existent_path)

            captured = capsys.readouterr()
            assert 'フォルダが見つかりません' in captured.out

    def test_open_folder_async_subprocess_error(self, tmp_path, capsys):
        """異常系: subprocess実行時にエラーが発生"""
        folder_path = str(tmp_path)

        with patch('service.heroku_login_again.time.sleep'), \
             patch('service.heroku_login_again.sys.platform', 'win32'), \
             patch('service.heroku_login_again.subprocess.run', side_effect=Exception("Process error")):

            open_folder_async(folder_path)

            captured = capsys.readouterr()
            assert 'フォルダを開く際にエラーが発生' in captured.out


class TestPromptHerokuLogin:
    """prompt_heroku_login関数のテスト"""

    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        config = {
            "Paths": {
                "executable_file_path": "C:\\test\\path"
            }
        }
        return config

    def test_prompt_heroku_login_success(self, mock_config, capsys):
        """正常系: Herokuログインプロセスが成功"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")
        mock_process.stdin = Mock()

        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread') as mock_thread, \
             patch('service.heroku_login_again.subprocess.Popen', return_value=mock_process), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

            captured = capsys.readouterr()
            assert 'Heroku CLIでログインを開始' in captured.out
            assert 'ログインプロセスが完了しました' in captured.out

    def test_prompt_heroku_login_failure(self, mock_config, capsys):
        """異常系: Herokuログインプロセスが失敗"""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Login failed")
        mock_process.stdin = Mock()

        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread'), \
             patch('service.heroku_login_again.subprocess.Popen', return_value=mock_process), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

            captured = capsys.readouterr()
            assert 'ログインプロセスが終了しました' in captured.out

    def test_prompt_heroku_login_timeout(self, mock_config, capsys):
        """異常系: ログインがタイムアウト"""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired('cmd', 120)
        mock_process.stdin = Mock()

        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread'), \
             patch('service.heroku_login_again.subprocess.Popen', return_value=mock_process), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

            captured = capsys.readouterr()
            assert 'ログインがタイムアウトしました' in captured.out
            mock_process.kill.assert_called_once()

    def test_prompt_heroku_login_exception(self, mock_config, capsys):
        """異常系: 予期しない例外が発生"""
        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread'), \
             patch('service.heroku_login_again.subprocess.Popen', side_effect=Exception("Unexpected error")), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

            captured = capsys.readouterr()
            assert 'ログイン処理中にエラーが発生しました' in captured.out

    def test_prompt_heroku_login_stdin_write_error(self, mock_config):
        """異常系: stdin書き込み時にエラーが発生しても続行"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")
        mock_process.stdin = Mock()
        mock_process.stdin.write.side_effect = Exception("Write error")

        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread'), \
             patch('service.heroku_login_again.subprocess.Popen', return_value=mock_process), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

    def test_prompt_heroku_login_thread_creation(self, mock_config):
        """正常系: フォルダオープン用のスレッドが作成される"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")
        mock_process.stdin = Mock()

        with patch('service.heroku_login_again.load_config', return_value=mock_config), \
             patch('service.heroku_login_again.threading.Thread') as mock_thread_class, \
             patch('service.heroku_login_again.subprocess.Popen', return_value=mock_process), \
             patch('service.heroku_login_again.time.sleep'):

            prompt_heroku_login()

            mock_thread_class.assert_called_once()
            thread_instance = mock_thread_class.return_value
            assert thread_instance.daemon is True
            thread_instance.start.assert_called_once()


class TestEnsureHerokuLogin:
    """ensure_heroku_login関数のテスト"""

    def test_ensure_heroku_login_already_logged_in(self):
        """正常系: 既にログインしている場合"""
        with patch('service.heroku_login_again.check_heroku_login', return_value=True):
            result = ensure_heroku_login()

            assert result is True

    def test_ensure_heroku_login_success_after_prompt(self, capsys):
        """正常系: ログインプロンプト後にログイン成功"""
        with patch('service.heroku_login_again.check_heroku_login', side_effect=[False, True]), \
             patch('service.heroku_login_again.prompt_heroku_login'):

            result = ensure_heroku_login()

            assert result is True
            captured = capsys.readouterr()
            assert 'Herokuログイン確認完了' in captured.out

    def test_ensure_heroku_login_failure_after_prompt(self, capsys):
        """異常系: ログインプロンプト後もログイン失敗"""
        with patch('service.heroku_login_again.check_heroku_login', return_value=False), \
             patch('service.heroku_login_again.prompt_heroku_login'):

            result = ensure_heroku_login()

            assert result is False
            captured = capsys.readouterr()
            assert 'Herokuへのログインに失敗しました' in captured.out

    def test_ensure_heroku_login_calls_prompt_when_not_logged_in(self):
        """正常系: ログインしていない場合にpromptが呼ばれる"""
        with patch('service.heroku_login_again.check_heroku_login', side_effect=[False, True]), \
             patch('service.heroku_login_again.prompt_heroku_login') as mock_prompt:

            ensure_heroku_login()

            mock_prompt.assert_called_once()

    def test_ensure_heroku_login_does_not_call_prompt_when_logged_in(self):
        """正常系: ログイン済みの場合にpromptが呼ばれない"""
        with patch('service.heroku_login_again.check_heroku_login', return_value=True), \
             patch('service.heroku_login_again.prompt_heroku_login') as mock_prompt:

            ensure_heroku_login()

            mock_prompt.assert_not_called()

    def test_ensure_heroku_login_check_called_twice_when_prompting(self):
        """正常系: ログインプロンプト時にcheckが2回呼ばれる"""
        with patch('service.heroku_login_again.check_heroku_login', side_effect=[False, True]) as mock_check, \
             patch('service.heroku_login_again.prompt_heroku_login'):

            ensure_heroku_login()

            assert mock_check.call_count == 2
