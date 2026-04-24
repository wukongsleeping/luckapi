from app.api.proxy import parse_authorization, _get_client_ip, _check_ip_whitelist


class TestParseAuthorization:
    """Tests for parse_authorization function."""

    def test_returns_bearer_token(self):
        token = parse_authorization("Bearer sk-test123")
        assert token == "sk-test123"

    def test_returns_raw_key_without_bearer(self):
        key = parse_authorization("sk-raw-key-123")
        assert key == "sk-raw-key-123"

    def test_returns_none_for_none_input(self):
        assert parse_authorization(None) is None

    def test_returns_none_for_empty_string(self):
        assert parse_authorization("") is None

    def test_handles_empty_bearer(self):
        token = parse_authorization("Bearer ")
        assert token == ""

    def test_case_sensitivity_bearer(self):
        """Bearer should be case-sensitive as per OpenAI convention."""
        result = parse_authorization("BEARER sk-test")
        assert result == "BEARER sk-test"

    def test_bearer_with_whitespace(self):
        token = parse_authorization("Bearer  double-space-key")
        assert token == " double-space-key"


class TestGetClientIp:
    """Tests for _get_client_ip function."""

    def test_returns_client_host_without_proxy(self, mock_request):
        ip = _get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_returns_forwarded_ip(self, mock_request):
        mock_request.headers = {"x-forwarded-for": "203.0.113.50"}
        ip = _get_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_returns_first_ip_from_multiple_forwarded(self, mock_request):
        mock_request.headers = {"x-forwarded-for": "203.0.113.50, 198.51.100.1, 10.0.0.1"}
        ip = _get_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_handles_no_client(self):
        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers = {}
        request.client = None
        ip = _get_client_ip(request)
        assert ip == "0.0.0.0"

    def test_returns_client_for_empty_forwarded(self, mock_request):
        # When x-forwarded-for is present but empty, falls back to client
        mock_request.headers = {"x-forwarded-for": ""}
        mock_request.headers["x-forwarded-for"] = ""
        ip = _get_client_ip(mock_request)
        # Empty string is falsy, so forwarded check fails, falls back to client
        assert ip == mock_request.client.host


class TestCheckIpWhitelist:
    """Tests for _check_ip_whitelist function."""

    def test_allows_none_allowed_ips(self):
        assert _check_ip_whitelist(None, "192.168.1.1") is True

    def test_allows_empty_allowed_ips(self):
        assert _check_ip_whitelist("", "192.168.1.1") is True

    def test_allows_whitespace_only(self):
        assert _check_ip_whitelist("  ", "192.168.1.1") is True

    def test_allows_single_matching_ip(self):
        assert _check_ip_whitelist("192.168.1.1", "192.168.1.1") is True

    def test_denies_non_matching_ip(self):
        assert _check_ip_whitelist("10.0.0.1", "192.168.1.1") is False

    def test_allows_ip_in_list(self):
        allowed = "10.0.0.1, 192.168.1.1, 172.16.0.1"
        assert _check_ip_whitelist(allowed, "172.16.0.1") is True

    def test_denies_ip_not_in_list(self):
        allowed = "10.0.0.1, 192.168.1.1"
        assert _check_ip_whitelist(allowed, "172.16.0.1") is False

    def test_handles_whitespace_in_ips(self):
        allowed = "  192.168.1.1 ,  10.0.0.1  "
        assert _check_ip_whitelist(allowed, "192.168.1.1") is True

    def test_exact_match_only(self):
        allowed = "192.168.1.1"
        assert _check_ip_whitelist(allowed, "192.168.1.10") is False
        assert _check_ip_whitelist(allowed, "192.168.1.11") is False
