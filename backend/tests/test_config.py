from app.core.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class and configuration."""

    def test_default_app_name(self):
        settings = Settings()
        assert settings.APP_NAME == "LuckApi"

    def test_default_app_version(self):
        settings = Settings()
        assert settings.APP_VERSION == "1.0.0"

    def test_default_mysql_config(self):
        settings = Settings()
        assert settings.MYSQL_HOST == "localhost"
        assert settings.MYSQL_PORT == 3306
        assert settings.MYSQL_DATABASE == "luckapi"

    def test_default_redis_config(self):
        settings = Settings()
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0

    def test_mysql_url_format(self):
        settings = Settings()
        assert "mysql+asyncmy://" in settings.mysql_url
        assert "@localhost:3306/luckapi" in settings.mysql_url

    def test_redis_url_without_password(self):
        settings = Settings()
        assert "redis://" in settings.redis_url
        assert "localhost" in settings.redis_url

    def test_redis_url_with_password(self):
        settings = Settings()
        settings.REDIS_PASSWORD = "mysecret"
        assert "redis://:mysecret@" in settings.redis_url

    def test_mysql_url_uses_custom_credentials(self):
        settings = Settings()
        settings.MYSQL_USER = "custom_user"
        settings.MYSQL_PASSWORD = "custom_pass"
        settings.MYSQL_DATABASE = "custom_db"
        assert "custom_user" in settings.mysql_url
        assert "custom_pass" in settings.mysql_url
        assert "custom_db" in settings.mysql_url

    def test_default_secret_key(self):
        settings = Settings()
        assert len(settings.SECRET_KEY) > 0

    def test_default_algorithm(self):
        settings = Settings()
        assert settings.ALGORITHM == "HS256"

    def test_default_proxy_prefix(self):
        settings = Settings()
        assert settings.PROXY_PREFIX == "/api/v1"

    def test_access_token_expire_minutes(self):
        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 2  # 2 days

    def test_custom_mysql_credentials(self):
        settings = Settings()
        settings.MYSQL_USER = "custom_user"
        settings.MYSQL_PASSWORD = "custom_pass"
        settings.MYSQL_DATABASE = "custom_db"
        assert "custom_user" in settings.mysql_url
        assert "custom_pass" in settings.mysql_url
        assert "custom_db" in settings.mysql_url

    def test_custom_redis_with_password(self):
        settings = Settings()
        settings.REDIS_HOST = "redis-cache.server.com"
        settings.REDIS_PORT = 6380
        settings.REDIS_PASSWORD = "secure"
        assert "redis-cache.server.com" in settings.redis_url
        assert "secure" in settings.redis_url

    def test_env_file_exists(self):
        """Verify the .env file path is relative to backend directory."""
        from pathlib import Path
        settings = Settings()
        env_file = Path(settings.Config.env_file)
        assert env_file.exists()

    def test_case_sensitive_config(self):
        """Verify case sensitivity is enabled."""
        assert Settings.Config.case_sensitive is True


class TestGetSettings:
    """Tests for get_settings caching."""

    def test_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caches_settings_instance(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # Same instance due to lru_cache
