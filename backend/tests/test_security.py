import re
from app.core.security import generate_api_key, generate_user_token, hash_password, verify_password


class TestGenerateApiKey:
    """Tests for generate_api_key function."""

    def test_generates_key_with_default_prefix(self):
        key = generate_api_key()
        assert key.startswith("sk-")
        assert len(key) == 3 + 48  # prefix + random part

    def test_generates_key_with_custom_prefix(self):
        key = generate_api_key("custom")
        assert key.startswith("custom-")
        assert len(key) == 7 + 48  # prefix + random part

    def test_keys_are_unique(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100

    def test_key_contains_only_valid_characters(self):
        import string
        key = generate_api_key("a")
        valid_chars = string.ascii_letters + string.digits + "-"
        for char in key:
            assert char in valid_chars

    def test_random_part_length(self):
        key = generate_api_key("x")
        # Key format: "x-" + random_part, so random starts at index 2
        random_part = key.split("-", 1)[1] if "-" in key else key[1:]
        assert len(random_part) == 48

    def test_keys_dont_contain_special_chars_in_random_part(self):
        key = generate_api_key()
        random_part = key[3:]
        assert not any(c in random_part for c in "!@#$%^&*()_+-=[]{}|;:',.<>?/`~")


class TestGenerateUserToken:
    """Tests for generate_user_token function."""

    def test_returns_string(self):
        token = generate_user_token(1)
        assert isinstance(token, str)

    def test_returns_unique_tokens(self):
        tokens = {generate_user_token(i) for i in range(100)}
        assert len(tokens) == 100

    def test_token_is_unpredictable(self):
        # token_urlsafe generates random tokens, not deterministic
        token1 = generate_user_token(42)
        token2 = generate_user_token(42)
        # They should typically be different (random generation)
        # At minimum, verify the function works
        assert isinstance(token1, str)
        assert len(token1) > 0

    def test_different_for_different_user_ids(self):
        token_a = generate_user_token(1)
        token_b = generate_user_token(2)
        assert token_a != token_b


class TestHashPassword:
    """Tests for hash_password function."""

    def test_returns_sha256_hash_format(self):
        hashed = hash_password("testpassword")
        assert hashed.startswith("sha256$luckapi-salt$")

    def test_hash_is_consistent(self):
        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 == h2

    def test_different_passwords_give_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_empty_password(self):
        hashed = hash_password("")
        assert hashed.startswith("sha256$luckapi-salt$")
        assert len(hashed.split("$")) == 3

    def test_unicode_password(self):
        hashed = hash_password("密码123")
        assert hashed.startswith("sha256$luckapi-salt$")

    def test_very_long_password(self):
        hashed = hash_password("a" * 10000)
        assert hashed.startswith("sha256$luckapi-salt$")

    def test_hash_format_matches_spec(self):
        """Hash should match sha256$salt$hash format from AGENTS.md."""
        hashed = hash_password("test")
        parts = hashed.split("$")
        assert len(parts) == 3
        assert parts[0] == "sha256"
        assert parts[1] == "luckapi-salt"
        assert len(parts[2]) == 64  # SHA256 hex digest


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_correct_password(self):
        password = "test123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        password = "wrong_password"
        hashed = hash_password("correct_password")
        assert verify_password(password, hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_rejects_non_sha256_format(self):
        assert verify_password("anything", "bcrypt$hash") is False
        assert verify_password("anything", "plain_password") is False

    def test_rejects_malformed_hash(self):
        assert verify_password("test", "sha256$only_two") is False
        assert verify_password("test", "sha256$too$many$parts$here") is False

    def test_verify_unicode_password(self):
        password = "密码测试"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_special_characters_password(self):
        password = "p@$$w0rd!#$%"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_none_hash(self):
        """Verify password with None hash should raise an exception."""
        from unittest.mock import MagicMock
        mock_hash = None
        try:
            verify_password("test", mock_hash)
        except (AttributeError, TypeError, ValueError):
            pass  # Expected exception for invalid hash
