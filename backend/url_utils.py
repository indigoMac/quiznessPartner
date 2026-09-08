"""Fetch public web pages and extract readable text for quiz generation."""

import ipaddress
import socket
from html.parser import HTMLParser
from io import BytesIO
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx

from ai_utils import extract_text_from_pdf

MAX_DOWNLOAD_BYTES = 1_000_000
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_REDIRECTS = 3
MIN_EXTRACTED_CHARS = 40
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata.google.com",
}
USER_AGENT = "QuizNess/1.0 (quiz generator; +https://quizness-partner.vercel.app)"


class UrlFetchError(Exception):
    """Raised when a URL cannot be fetched or is not allowed."""


class _HTMLTextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr", "section"}:
            self.body_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        else:
            self.body_parts.append(data)


def _ip_is_blocked(address) -> bool:
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _hostname_is_blocked(hostname: str) -> bool:
    host = hostname.strip("[]").lower().rstrip(".")
    if not host:
        return True
    if host in BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        return True
    try:
        return _ip_is_blocked(ipaddress.ip_address(host))
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UrlFetchError("Could not resolve that URL.") from exc

    if not infos:
        raise UrlFetchError("Could not resolve that URL.")

    for info in infos:
        ip_text = info[4][0]
        try:
            if _ip_is_blocked(ipaddress.ip_address(ip_text)):
                return True
        except ValueError:
            return True
    return False


def validate_public_http_url(url: str) -> str:
    """Return a normalized public http(s) URL or raise UrlFetchError."""
    raw = (url or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise UrlFetchError("Enter a public http or https URL.")
    if parsed.username or parsed.password:
        raise UrlFetchError("This URL is not allowed.")
    hostname = parsed.hostname
    if not hostname or _hostname_is_blocked(hostname):
        raise UrlFetchError("This URL is not allowed.")
    return raw


def _extract_html(content: str) -> Tuple[str, Optional[str]]:
    parser = _HTMLTextExtractor()
    parser.feed(content)
    parser.close()
    title = " ".join(" ".join(parser.title_parts).split()) or None
    text = " ".join("".join(parser.body_parts).split())
    return text, title


def _read_limited_body(response: httpx.Response) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_DOWNLOAD_BYTES:
                raise UrlFetchError("That page is too large to import.")
        except ValueError:
            pass

    chunks = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > MAX_DOWNLOAD_BYTES:
            raise UrlFetchError("That page is too large to import.")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_url_text(url: str) -> Tuple[str, Optional[str]]:
    """Download a public page and return (text, page_title)."""
    current = validate_public_http_url(url)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/pdf,text/plain",
    }

    with httpx.Client(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
        headers=headers,
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            validate_public_http_url(current)
            try:
                with client.stream("GET", current) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise UrlFetchError("Could not fetch that URL.")
                        current = urljoin(str(response.url), location)
                        continue
                    if response.status_code in {401, 403}:
                        raise UrlFetchError(
                            "That page could not be read. It may require login."
                        )
                    if response.status_code == 404:
                        raise UrlFetchError("That page was not found.")
                    if response.status_code >= 400:
                        raise UrlFetchError("Could not fetch that URL.")

                    content_type = (
                        response.headers.get("content-type", "").split(";")[0].lower()
                    )
                    body = _read_limited_body(response)
            except httpx.HTTPError as exc:
                raise UrlFetchError("Could not fetch that URL.") from exc

            if content_type in {"application/pdf"} or current.lower().endswith(".pdf"):
                text = extract_text_from_pdf(BytesIO(body))
                return text.strip(), None

            encoding = response.encoding or "utf-8"
            try:
                decoded = body.decode(encoding, errors="replace")
            except LookupError:
                decoded = body.decode("utf-8", errors="replace")

            if content_type in {"text/plain"}:
                text = decoded.strip()
                if len(text) < MIN_EXTRACTED_CHARS:
                    raise UrlFetchError(
                        "Could not extract enough readable text from that page."
                    )
                return text, None

            text, title = _extract_html(decoded)
            if len(text) < MIN_EXTRACTED_CHARS:
                raise UrlFetchError(
                    "Could not extract enough readable text from that page."
                )
            return text, title

    raise UrlFetchError("That URL redirected too many times.")
