#!/usr/bin/env python3
"""
Server-side availability updater for the Northeast Campsite Finder.

Reads the Recreation.gov campground IDs directly out of index.html (so the two
never drift apart), fetches per-site availability for the next ~4 months, and
writes availability.json next to index.html. The site's frontend reads that
file and shows live badges to every visitor with no client-side API calls.

Run by .github/workflows/availability.yml every 30 minutes.
"""
import datetime
import json
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
OUT = ROOT / "availability.json"

MONTHS_AHEAD = 4          # coverage horizon (~120 days)
REQUEST_DELAY_S = 1.2     # be polite to recreation.gov
EXCLUDE_TYPES = re.compile(r"GROUP|MANAGEMENT|EQUESTRIAN", re.I)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36 northeast-campsite-finder (personal project)")


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def month_starts(base: datetime.date, n: int):
    y, m = base.year, base.month
    for _ in range(n):
        yield datetime.date(y, m, 1)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main() -> int:
    rec_ids = sorted(set(re.findall(r"recId:(\d+)", INDEX.read_text())))
    if not rec_ids:
        print("No recId entries found in index.html", file=sys.stderr)
        return 1

    base = datetime.date.today()
    horizon = MONTHS_AHEAD * 31
    camps, failures = {}, []

    for rec_id in rec_ids:
        sites: dict[str, list[int]] = {}
        try:
            for mstart in month_starts(base, MONTHS_AHEAD):
                url = (f"https://www.recreation.gov/api/camps/availability/campground/"
                       f"{rec_id}/month?start_date={mstart:%Y-%m}-01T00%3A00%3A00.000Z")
                data = get_json(url)
                for site_id, site in (data.get("campsites") or {}).items():
                    if EXCLUDE_TYPES.search(site.get("campsite_type") or ""):
                        continue
                    for stamp, status in (site.get("availabilities") or {}).items():
                        if status != "Available":
                            continue
                        day = datetime.date.fromisoformat(stamp[:10])
                        off = (day - base).days
                        if 0 <= off < horizon:
                            sites.setdefault(site_id, []).append(off)
                time.sleep(REQUEST_DELAY_S)
            camps[rec_id] = {"sites": {k: sorted(set(v)) for k, v in sites.items()}}
            open_sites = sum(1 for v in sites.values() if v)
            print(f"  {rec_id}: {len(sites)} sites, {open_sites} with any availability")
        except Exception as exc:  # keep going; one bad campground shouldn't kill the run
            failures.append(rec_id)
            print(f"  {rec_id}: FAILED ({exc})", file=sys.stderr)

    if not camps:
        print("Every campground fetch failed — keeping previous availability.json", file=sys.stderr)
        return 1

    OUT.write_text(json.dumps({
        "generated": int(time.time() * 1000),
        "base": base.isoformat(),
        "horizon": horizon,
        "camps": camps,
        "failed": failures,
    }, separators=(",", ":")))
    print(f"Wrote {OUT.name}: {len(camps)} campgrounds ok, {len(failures)} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
