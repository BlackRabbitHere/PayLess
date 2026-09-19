import logging
import threading
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import HttpFetcher
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.providers.base import ProviderConfig


class ConservativeRobotsParser(RobotFileParser):
    """Combine matching groups and use the longest rule, independent of file order.

    urllib uses first-match rules (unsafe for Yatra's leading Allow: /). Unsupported
    wildcard/end-anchor paths fail closed rather than silently ignoring restrictions.
    """

    def __init__(self):
        super().__init__()
        self.groups = []

    def _add_entry(self, entry):
        self.groups.append(entry)
        super()._add_entry(entry)

    def parse(self, lines):
        normalized = []
        for line in lines:
            key, separator, value = line.split("#", 1)[0].partition(":")
            # EaseMyTrip publishes Allow: *. Its universal meaning is unambiguous.
            if separator and key.strip().lower() in {"allow", "disallow"} and value.strip() == "*":
                line = key + ": /"
            normalized.append(line)
        super().parse(normalized)

    def matching_groups(self, useragent):
        specific = [
            entry for entry in self.groups
            if any(agent != "*" and agent.lower() in useragent.split("/")[0].lower()
                   for agent in entry.useragents)
        ]
        return specific or [entry for entry in self.groups if "*" in entry.useragents]

    def can_fetch(self, useragent, url):
        rules = [rule for entry in self.matching_groups(useragent) for rule in entry.rulelines]
        if any("%2A" in rule.path.upper() or "%24" in rule.path.upper() for rule in rules):
            raise ScraperError(ErrorCode.SOURCE_UNAVAILABLE, "Unsupported robots pattern; access denied.")
        # Delegate URL canonicalization to urllib after sorting by specificity.
        from urllib.robotparser import Entry

        merged = Entry()
        merged.useragents = ["*"]
        merged.rulelines = sorted(rules, key=lambda rule: (len(rule.path), rule.allowance), reverse=True)
        checker = RobotFileParser()
        checker.default_entry = merged
        checker.modified()
        return checker.can_fetch(useragent, url)

    def crawl_delay(self, useragent):
        return max((entry.delay or 0 for entry in self.matching_groups(useragent)), default=0)

    def request_rate(self, useragent):
        rates = [entry.req_rate for entry in self.matching_groups(useragent) if entry.req_rate]
        return max(rates, key=lambda rate: rate.seconds / rate.requests, default=None)


class SourceAccess:
    """Activation is configuration; robots/terms are informational, never legal permission."""

    def __init__(self, settings: Settings, fetcher: HttpFetcher, *, clock=time.monotonic):
        self.settings, self.fetcher, self.clock = settings, fetcher, clock
        self._robots = {}
        self._lock = threading.RLock()
        self.metadata = {}

    def check_terms(self, config: ProviderConfig):
        # Retain the method for callers, but do not conflate review with activation.
        if not getattr(self.settings, f"provider_{config.provider.value.lower()}_enabled"):
            raise ScraperError(
                ErrorCode.PROVIDER_DISABLED, "Provider disabled by application configuration.",
            )

    def check(self, url: str, policy: UrlPolicy):
        with self._lock:
            policy.validate(url)
            origin = f"https://{urlsplit(url).netloc}"
            cached = self._robots.get(origin)
            if not cached or cached[0] <= self.clock():
                parser = None
                try:
                    result = self.fetcher.fetch(
                        origin + "/robots.txt", policy, allowed_types=("text/plain", "text/html"),
                        force_refresh=True, accepted_statuses=frozenset({404, 410}),
                    )
                    parser = ConservativeRobotsParser()
                    parser.parse([] if result.status in (404, 410) else result.html.splitlines())
                    provider = urlsplit(url).hostname.split(".")[-2].upper()
                    SnapshotStore(self.settings).save(provider, "ACCESS_REVIEW", result)
                except (ScraperError, OSError) as exc:
                    self.metadata[origin] = {"error": str(exc), "informationalOnly": True}
                    logging.getLogger(__name__).warning("robots_unavailable", extra={"url": url})
                cached = (self.clock() + self.settings.robots_cache_seconds, parser)
                self._robots[origin] = cached
            parser = cached[1]
            if parser is not None:
                try:
                    allowed = parser.can_fetch(self.settings.scraper_user_agent, url)
                except ScraperError:
                    allowed = None
                self.metadata[url] = {
                    "allowed": allowed, "crawlDelay": parser.crawl_delay(self.settings.scraper_user_agent),
                    "informationalOnly": True,
                }
                logging.getLogger(__name__).info(
                    "robots_observed", extra={"url": url, "robotsMetadata": self.metadata[url]},
                )
