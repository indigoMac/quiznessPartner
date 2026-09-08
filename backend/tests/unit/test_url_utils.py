import json
from unittest.mock import MagicMock, patch

import pytest

from url_utils import (
    UrlFetchError,
    _extract_html,
    fetch_url_text,
    validate_public_http_url,
)


def test_rejects_non_http_urls():
    with pytest.raises(UrlFetchError, match="http or https"):
        validate_public_http_url("file:///etc/passwd")
    with pytest.raises(UrlFetchError, match="http or https"):
        validate_public_http_url("ftp://example.com/file")
    with pytest.raises(UrlFetchError, match="http or https"):
        validate_public_http_url("not a url")


def test_rejects_localhost_and_private_ips():
    with pytest.raises(UrlFetchError, match="not allowed"):
        validate_public_http_url("http://localhost/admin")
    with pytest.raises(UrlFetchError, match="not allowed"):
        validate_public_http_url("http://127.0.0.1/secret")
    with pytest.raises(UrlFetchError, match="not allowed"):
        validate_public_http_url("http://10.0.0.4/notes")
    with pytest.raises(UrlFetchError, match="not allowed"):
        validate_public_http_url("http://169.254.169.254/latest/meta-data")


def test_rejects_userinfo_in_url():
    with pytest.raises(UrlFetchError, match="not allowed"):
        validate_public_http_url("https://user:pass@example.com/page")


def test_extract_html_strips_scripts_and_reads_title():
    html = """
    <html>
      <head><title> Photosynthesis Notes </title></head>
      <body>
        <script>window.alert('nope')</script>
        <p>Plants convert sunlight into energy through photosynthesis.</p>
      </body>
    </html>
    """
    text, title = _extract_html(html)
    assert title == "Photosynthesis Notes"
    assert "Plants convert sunlight" in text
    assert "alert" not in text


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str = "text/html", status_code: int = 200):
        self.status_code = status_code
        self.is_redirect = False
        self.encoding = "utf-8"
        self.headers = {"content-type": content_type}
        self.url = "https://example.com/article"
        self._body = body

    def iter_bytes(self):
        yield self._body


@patch("url_utils.socket.getaddrinfo")
@patch("url_utils.httpx.Client")
def test_fetch_url_text_reads_html(mock_client_cls, mock_getaddrinfo):
    mock_getaddrinfo.return_value = [(0, 0, 0, 0, ("93.184.216.34", 0))]
    html = (
        b"<html><head><title>Cell Biology</title></head>"
        b"<body><p>" + b"Cells are the basic unit of life. " * 8 + b"</p></body></html>"
    )
    fake = _FakeResponse(html)
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_stream = MagicMock()
    mock_stream.__enter__.return_value = fake
    mock_client.stream.return_value = mock_stream

    text, title = fetch_url_text("https://example.com/article")
    assert title == "Cell Biology"
    assert "Cells are the basic unit of life" in text
    mock_client.stream.assert_called_once()
