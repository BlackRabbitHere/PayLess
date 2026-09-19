"""Start real Uvicorn, check HTTP endpoints, then clean up. Fixture mode is the default."""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--live", action="store_true", help="Use actual provider HTTP; never fixture fallback.")
parser.add_argument("--provider", default="GYFTR", choices=("GYFTR", "YATRA", "EASEMYTRIP"))
parser.add_argument("--merchant", default="SWIGGY")
args = parser.parse_args()
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
env = {
    **os.environ,
    "FIXTURE_DIR": "" if args.live else str(root / "tests" / "fixtures"),
    "SAVE_RAW_HTML": "true" if args.live else "false",
}
creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "payment_scraper.api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ],
    cwd=root,
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=creationflags,
)
origin = f"http://127.0.0.1:{port}"
try:
    deadline = time.monotonic() + 15
    while True:
        try:
            with urlopen(origin + "/health", timeout=1) as response:
                assert json.load(response)["status"] == "ok"
            break
        except URLError:
            if time.monotonic() > deadline or process.poll() is not None:
                raise RuntimeError("Uvicorn did not become healthy")
            time.sleep(0.1)
    with urlopen(origin + "/docs", timeout=5) as response:
        assert b"swagger-ui" in response.read()
    with urlopen(origin + "/openapi.json", timeout=5) as response:
        assert "/api/v1/scrape" in json.load(response)["paths"]
    print("Real Uvicorn HTTP: health, Swagger and OpenAPI passed", flush=True)
    request = Request(
        origin + "/api/v1/scrape",
        data=json.dumps({
            "provider": args.provider, "merchant": args.merchant, "forceRefresh": True,
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180 if args.live else 5) as response:
            data = json.load(response)
    except HTTPError as exc:
        data = json.load(exc)
    if args.live:
        folder = root / "data" / "verification"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"api_{args.provider.lower()}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps(data, indent=2))
        assert not data["metadata"]["fixture"]
        if not data["offers"] or data["errors"]:
            raise SystemExit("LIVE OFFER CHECK FAILED; see structured response above.")
        assert data["metadata"]["fetchMethod"] in {"HTTP", "BROWSER"}
        print("Real Uvicorn LIVE offer check passed")
    else:
        assert data["metadata"]["fixture"] and data["offers"]
        if args.provider == "GYFTR":
            assert data["offers"][0]["voucher"]["sellingPrice"] == "487.50"
        print("Real Uvicorn FIXTURE offer check passed")
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
