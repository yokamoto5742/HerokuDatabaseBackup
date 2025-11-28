from utils.database_helper import add_ssl_mode


class TestAddSslMode:
    """add_ssl_mode関数のテスト"""

    def test_add_ssl_mode_without_query_params(self):
        """正常系: クエリパラメータがない場合、?を追加してsslmodeを付与"""
        database_url = "postgresql://user:pass@localhost:5432/testdb"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://user:pass@localhost:5432/testdb?sslmode=require"
        assert "?sslmode=require" in result
        assert "&" not in result

    def test_add_ssl_mode_with_existing_query_params(self):
        """正常系: 既存のクエリパラメータがある場合、&を追加してsslmodeを付与"""
        database_url = "postgresql://user:pass@localhost:5432/testdb?option=value"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://user:pass@localhost:5432/testdb?option=value&sslmode=require"
        assert "&sslmode=require" in result
        assert result.count("?") == 1

    def test_add_ssl_mode_with_multiple_query_params(self):
        """正常系: 複数のクエリパラメータがある場合、&で追加"""
        database_url = "postgresql://user:pass@localhost:5432/testdb?param1=val1&param2=val2"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://user:pass@localhost:5432/testdb?param1=val1&param2=val2&sslmode=require"
        assert result.endswith("&sslmode=require")

    def test_add_ssl_mode_preserves_original_url(self):
        """正常系: 元のURLが変更されず、末尾にsslmodeが追加される"""
        database_url = "postgresql://user:pass@host.com:1234/db"
        result = add_ssl_mode(database_url)

        assert result.startswith(database_url)
        assert database_url in result
        assert len(result) > len(database_url)

    def test_add_ssl_mode_empty_string(self):
        """異常系: 空文字列の場合"""
        result = add_ssl_mode("")
        assert result == "?sslmode=require"

    def test_add_ssl_mode_postgres_scheme(self):
        """正常系: postgres://スキームでも動作する"""
        database_url = "postgres://user:pass@localhost:5432/testdb"
        result = add_ssl_mode(database_url)

        assert result == "postgres://user:pass@localhost:5432/testdb?sslmode=require"

    def test_add_ssl_mode_with_port_only(self):
        """正常系: ポート番号のみのシンプルなURL"""
        database_url = "postgresql://localhost:5432/db"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://localhost:5432/db?sslmode=require"

    def test_add_ssl_mode_idempotent(self):
        """正常系: 複数回適用しても安全（既存のsslmodeは考慮しない）"""
        database_url = "postgresql://user:pass@localhost:5432/testdb?sslmode=prefer"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://user:pass@localhost:5432/testdb?sslmode=prefer&sslmode=require"
        assert result.count("sslmode") == 2

    def test_add_ssl_mode_special_characters_in_password(self):
        """正常系: パスワードに特殊文字が含まれる場合"""
        database_url = "postgresql://user:p@ss%40word@localhost:5432/testdb"
        result = add_ssl_mode(database_url)

        assert result == "postgresql://user:p@ss%40word@localhost:5432/testdb?sslmode=require"
        assert "p@ss%40word" in result

    def test_add_ssl_mode_returns_string(self):
        """正常系: 戻り値が文字列型である"""
        database_url = "postgresql://user:pass@localhost:5432/testdb"
        result = add_ssl_mode(database_url)

        assert isinstance(result, str)
