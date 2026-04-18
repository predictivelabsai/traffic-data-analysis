"""Playwright smoke-tests + screenshot capture for the Devon Traffic dashboard.

Run:
    # in one terminal:
    devon-traffic serve --port 5001
    # in another:
    python -m pytest tests/test_playwright.py
    # or as a standalone script to regenerate screenshots + GIF:
    python tests/test_playwright.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"

ROUTES = [
    ("/",        "01-overview.png"),
    ("/od",      "02-od.png"),
    ("/speed",   "03-speed.png"),
    ("/journey", "04-journey.png"),
    ("/map",     "05-map.png"),
    ("/sources", "06-sources.png"),
]


def _capture_all(base_url: str = "http://127.0.0.1:5001") -> None:
    from playwright.sync_api import sync_playwright

    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        for route, filename in ROUTES:
            page.goto(f"{base_url}{route}", wait_until="networkidle")
            page.wait_for_timeout(2000)  # let Plotly finish drawing
            page.screenshot(path=str(SHOTS / filename), full_page=True)
            print(f"  captured {route} -> {filename}")
        browser.close()


@pytest.mark.parametrize("route,_", ROUTES)
def test_route_returns_200(route: str, _: str) -> None:
    """Each dashboard route responds 200 (requires server running on :5001)."""
    import urllib.request
    with urllib.request.urlopen(f"http://127.0.0.1:5001{route}", timeout=5) as r:
        assert r.status == 200


def test_capture_screenshots_and_build_gif() -> None:
    """End-to-end: screenshot each route, then rebuild the animated GIF."""
    _capture_all()
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "make_gif.py")])
    assert (ROOT / "docs" / "dashboard.gif").exists()


if __name__ == "__main__":
    _capture_all()
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "make_gif.py")])
