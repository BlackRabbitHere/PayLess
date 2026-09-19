import logging
import re

from bs4 import BeautifulSoup

from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.exceptions import ScraperError


def reject_access_challenge(html: str, status: int = 200, *, browser=False) -> None:
    """Detect challenge pages, not incidental words in ordinary offer terms."""
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True).casefold() if soup.title else ""
    blocked_titles = {
        "access denied",
        "403 forbidden",
        "forbidden",
        "request blocked",
        "unusual traffic",
        "bot verification",
        "captcha",
        "just a moment...",
        "attention required! | cloudflare",
        "verify you are human",
        "robot check",
        "checking your browser",
        "too many requests",
        "service unavailable",
        "sign in to continue",
        "login required",
    }
    heading = soup.select_one("h1")
    heading_text = heading.get_text(" ", strip=True).casefold() if heading else ""
    challenge = soup.select_one(
        "#challenge-form, #captcha, form[action*='captcha'], .g-recaptcha, .h-captcha"
    )
    visible = soup.get_text(" ", strip=True)
    body_challenge = re.match(
        r"^(?:access denied|403 forbidden|request blocked|checking your browser|verify you are human|"
        r"too many requests|service unavailable|please log in to continue|login required|captcha)\b",
        visible, re.I,
    )
    if (any(title.startswith(value) or heading_text.startswith(value) for value in blocked_titles)
            or challenge or body_challenge):
        logging.getLogger(__name__).warning(
            "blocked_page", extra={"httpStatus": status, "blockedReason": "access_challenge"}
        )
        raise ScraperError(
            ErrorCode.BROWSER_BLOCK_PAGE if browser else ErrorCode.BLOCK_PAGE,
            "Provider returned an access, login or CAPTCHA challenge; no interaction attempted.",
        )
    # One ordinary browser attempt may render a JS shell; it never solves a challenge.
    if title in {"enable javascript", "javascript required", "please enable javascript"}:
        logging.getLogger(__name__).warning(
            "blocked_page", extra={"httpStatus": status, "blockedReason": "javascript_required"}
        )
        raise ScraperError(ErrorCode.JS_RENDER_REQUIRED, "Provider requires JavaScript rendering.")
