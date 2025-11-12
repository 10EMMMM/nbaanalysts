# type: ignore
"""
Scrape NBA.com team stats tables (e.g., in-game split) via headless Playwright.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Sequence

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

NBA_URL_TEMPLATE = (
    "https://www.nba.com/stats/team/{team_id}/traditional"
    "?Season={season}&Split={split}&PerMode={per_mode}"
)


def scrape_table(url: str, wait_selector: str = "nba-stat-table table") -> tuple[List[str], List[List[str]]]:
    """Return headers and rows for the main stats table at the given URL."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector(wait_selector, timeout=60_000)

        headers = [
            cell.inner_text().strip()
            for cell in page.query_selector_all("nba-stat-table thead th")
            if cell.inner_text().strip()
        ]

        rows: List[List[str]] = []
        for tr in page.query_selector_all("nba-stat-table tbody tr"):
            cells = [td.inner_text().strip() for td in tr.query_selector_all("td")]
            if any(cells):
                rows.append(cells)

        browser.close()
        return headers, rows


def write_csv(headers: Sequence[str], rows: Sequence[Sequence[str]], output_path: Path) -> None:
    """Persist headers/rows to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape NBA.com team in-game split stats.")
    parser.add_argument("--team", required=True, help="Team ID (e.g., 1610612761 for OKC).")
    parser.add_argument("--season", default="2020-21", help="Season string (default 2020-21).")
    parser.add_argument("--split", default="ingame", help="Split parameter (default 'ingame').")
    parser.add_argument("--per-mode", default="PerGame", help="PerMode parameter (default 'PerGame').")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw"),
        help="Output file or directory for the CSV. If directory, filename is auto-generated.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = NBA_URL_TEMPLATE.format(
        team_id=args.team,
        season=args.season,
        split=args.split,
        per_mode=args.per_mode,
    )
    try:
        headers, rows = scrape_table(url)
    except PlaywrightTimeoutError as exc:
        raise SystemExit(f"Timed out scraping nba.com stats table: {exc}") from exc

    if not rows:
        raise SystemExit("No stats rows found; check team/season parameters.")

    output = args.output
    if output.is_dir() or output.suffix == "":
        filename = f"team_{args.team}_{args.season}_{args.split}_{args.per_mode}.csv"
        output = output / filename

    write_csv(headers, rows, output)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
