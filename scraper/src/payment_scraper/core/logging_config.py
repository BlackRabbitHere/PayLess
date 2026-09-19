import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

scrape_context: ContextVar[dict] = ContextVar("scrape_context", default={})


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            **scrape_context.get(),
        }
        for name in (
            "requestId",
            "provider",
            "merchant",
            "fetchMethod",
            "httpStatus",
            "durationMs",
            "offersFound",
            "verificationStatus",
            "cacheHit",
            "domain",
            "url",
            "waitSeconds",
            "blockedReason",
            "startTime", "endTime", "host", "finalUrl", "contentType", "responseBytes",
            "redirectChain", "httpExceptionType", "browserFallbackAttempted", "snapshotPath",
            "title", "selectorMissing", "robotsMetadata", "offersExcluded", "verificationSummary",
        ):
            if hasattr(record, name):
                data[name] = getattr(record, name)
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def configure_logging(level: str):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("payment_scraper")
    logger.handlers = [handler]
    logger.setLevel(level.upper())
    logger.propagate = False
