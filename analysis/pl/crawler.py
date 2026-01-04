#!/usr/bin/env python3
"""
Simple crawler to read match ids from matches.log (one per line), fetch
JSON from https://esports.wanmei.com/inframe/match-stats?match_id=<id>,
and save all responses into matches.json as a JSON array.

Usage:
    python3 0.crawler.py          # run with default 5s delay and real requests
    python3 0.crawler.py --dry-run  # only parse and show IDs without network
    python3 0.crawler.py --delay 2  # override delay in seconds

The script uses only the Python standard library (urllib) so no extra deps.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import tempfile
from typing import List, Any, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_LOG = os.path.join(BASE_DIR, "matches.log")
OUTPUT_FILE = os.path.join(BASE_DIR, "matches.json")
URL_TEMPLATE = "https://esports.wanmei.com/inframe/match-stats?match_id={id}"

ID_RE = re.compile(r"(\d+)")


def read_ids_from_file(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"matches log not found: {path}")
    ids = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            m = ID_RE.search(line)
            if m:
                ids.append(m.group(1))
            else:
                # if the line isn't purely numeric, still include it as-is
                ids.append(line)
    return ids


def fetch_json_for_id(id_: str, timeout: int = 20) -> Any:
    url = URL_TEMPLATE.format(id=id_)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; thucs2pl-crawler/1.0)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://esports.wanmei.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            # Try to decode as utf-8, fallback to latin1
            try:
                text = raw.decode("utf-8")
            except Exception:
                text = raw.decode("latin1")

            # If content-type indicates json, parse it. Otherwise try to parse anyway.
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # not valid json
                raise ValueError(f"Response for id={id_} is not valid JSON; content-type={content_type}")
            return data
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error for id={id_}: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error for id={id_}: {e}")


def atomic_write_json(obj: Any, path: str) -> None:
    # Write JSON to a temp file in the same directory then replace to avoid corruption on interrupt
    dirpath = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(prefix=".tmp_matches_json_", dir=dirpath)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def load_existing_results(path: str) -> List[Any]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except Exception:
        # If file is corrupted or unreadable, ignore and start fresh
        return []


# keep compatibility name
def save_results(results: List[Any], path: str) -> None:
    atomic_write_json(results, path)


def gather_processed_ids(results: List[Any]) -> List[str]:
    seen = []
    for item in results:
        if isinstance(item, dict):
            mid = item.get('match_id') or item.get('id')
            if isinstance(mid, (int, str)):
                seen.append(str(mid))
        # other types are ignored
    return seen


def run_crawler(ids: List[str], output_file: str, delay: float = 1.0) -> Tuple[List[Any], bool]:
    """
    Crawls match data for the given IDs.

    :param ids: List of match IDs to crawl.
    :param output_file: Path to the output JSON file.
    :param delay: Delay between requests.
    :return: A tuple containing the results and a boolean indicating if there were errors.
    """
    print(f"Found {len(ids)} ids. Delay: {delay}s")

    existing = load_existing_results(output_file)
    results = list(existing)
    processed = set(gather_processed_ids(existing))
    has_errors = False

    print(f"Resuming with {len(processed)} already-processed ids")

    for idx, id_ in enumerate(ids, start=1):
        if id_ in processed:
            print(f"[{idx}/{len(ids)}] Skipping already processed id={id_}")
            continue
        print(f"[{idx}/{len(ids)}] Processing id={id_}")
        try:
            data = fetch_json_for_id(id_)
        except Exception as e:
            print(f"  Error fetching id={id_}: {e}", file=sys.stderr)
            results.append({"match_id": id_, "error": str(e)})
            has_errors = True
        else:
            if isinstance(data, dict) and "match_id" not in data:
                data.setdefault("match_id", id_)
            results.append(data)

        try:
            save_results(results, output_file)
        except Exception as e:
            print(f"  Failed to write progress to {output_file}: {e}", file=sys.stderr)

        processed.add(id_)

        if idx < len(ids):
            print(f"  Sleeping {delay}s...")
            time.sleep(delay)

    print(f"Saved {len(results)} items to {output_file}")
    return results, has_errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Crawler for match JSONs")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait between requests (default 5)")
    parser.add_argument("--dry-run", action="store_true", help="parse IDs but do not perform HTTP requests")
    parser.add_argument("--input", default=MATCHES_LOG, help="path to matches.log")
    parser.add_argument("--output", default=OUTPUT_FILE, help="output JSON file path")
    args = parser.parse_args(argv)

    try:
        ids = read_ids_from_file(args.input)
    except Exception as e:
        print(f"Error reading ids: {e}", file=sys.stderr)
        sys.exit(2)

    if not ids:
        print("No match ids found in the input file.")
        save_results([], args.output)
        print(f"Wrote empty JSON array to {args.output}")
        return

    if args.dry_run:
        print(f"Found {len(ids)} ids. Dry run: {args.dry_run}. Delay: {args.delay}s")
        for idx, id_ in enumerate(ids, start=1):
            print(f"[{idx}/{len(ids)}] Would process id={id_}")
        return

    run_crawler(ids, args.output, args.delay)


if __name__ == "__main__":
    main()
