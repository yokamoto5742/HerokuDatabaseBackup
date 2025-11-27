def add_ssl_mode(database_url: str) -> str:
    """データベースURLにSSLモードを追加"""
    separator = "&" if "?" in database_url else "?"
    return f"{database_url}{separator}sslmode=require"
