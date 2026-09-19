import argparse
import sys
from pathlib import Path

from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ScrapeStatus
from payment_scraper.core.logging_config import configure_logging
from payment_scraper.output.json_writer import write_json
from payment_scraper.services.scraping_service import build_service


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Collect public payment offers.")
    sub = parser.add_subparsers(dest="command", required=True)
    scrape = sub.add_parser("scrape")
    scrape.add_argument("--provider", required=True)
    scrape.add_argument("--merchant", required=True)
    scrape.add_argument("--force-refresh", action="store_true")
    scrape.add_argument("--fixture-dir", type=Path, help="Explicit synthetic offline mode (never live data).")
    scrape.add_argument("--output", type=Path)
    scrape.add_argument("--json", action="store_true", help="Print the canonical JSON envelope to stdout.")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.fixture_dir:
        settings = Settings.model_validate({**settings.model_dump(), "fixture_dir": args.fixture_dir})
    configure_logging(settings.log_level)
    service = build_service(settings)
    try:
        result = service.scrape(args.provider, args.merchant, args.force_refresh)
    finally:
        service.close()
    if args.output:
        write_json(result, args.output)
    if args.json:
        print(result.model_dump_json(by_alias=True, indent=2))
    else:
        print(f"Provider: {result.provider}\nMerchant: {result.merchant}\nStatus: {result.status}")
        if result.metadata.fixture:
            print("SYNTHETIC FIXTURE DATA — not a live offer")
        print(f"Offers detected: {len(result.offers)}")
        for offer in result.offers:
            print(f"\n{offer.title}\nStatus: {offer.verification_status}")
            if offer.voucher:
                face, price = offer.voucher.face_value, offer.voucher.selling_price
                print(f"Face value: INR {face}\nSelling price: INR {price}")
                if face is not None and price is not None:
                    print(f"Saving: INR {face - price:.2f}")
            if offer.discount.value is not None:
                print(f"Discount: {offer.discount.value} ({offer.discount.type})")
        for error in result.errors:
            print(f"{error.code}: {error.message}")
        if settings.save_raw_html:
            print(
                f"Snapshots: {settings.data_dir / 'raw' / result.provider.lower() / result.merchant.lower()}"
            )
        if args.output:
            print(f"Normalized output: {args.output}")
    return 0 if result.status == ScrapeStatus.SUCCESS else 2 if result.status == ScrapeStatus.PARTIAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
