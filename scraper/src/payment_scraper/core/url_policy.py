import ipaddress
import socket
from urllib.parse import urlsplit

from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.exceptions import ScraperError


class UrlPolicy:
    def __init__(self, domains: frozenset[str], *, resolver=socket.getaddrinfo):
        self.domains = domains
        self.resolver = resolver

    def validate(self, url: str, *, resolve: bool = True) -> str:
        try:
            parts = urlsplit(url)
            if (
                parts.scheme != "https"
                or parts.hostname not in self.domains
                or parts.username
                or parts.password
                or parts.port not in (None, 443)
                or "\\" in url
                or any(ord(c) < 32 for c in url)
            ):
                raise ValueError("Not an approved HTTPS source.")
            host = parts.hostname
            if resolve:
                addresses = self.resolver(host, 443, type=socket.SOCK_STREAM)
                if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
                    raise ValueError("Source resolved to a nonpublic address.")
            return host
        except socket.gaierror as exc:
            raise ScraperError(
                ErrorCode.DNS_ERROR, "Source DNS lookup failed.", retryable=True
            ) from exc
        except ValueError as exc:
            raise ScraperError(
                ErrorCode.URL_NOT_ALLOWED, "URL is outside the approved public sources."
            ) from exc
