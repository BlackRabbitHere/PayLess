import os
import tempfile
from pathlib import Path

from payment_scraper.core.models import ScrapeResponse


def write_json(result: ScrapeResponse, destination: Path) -> Path:
    """Atomic replacement prevents consumers observing a partial JSON document."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(result.model_dump_json(by_alias=True, indent=2))
            stream.write("\n")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
