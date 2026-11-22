"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone

from . import __version__
from .report import render_json, render_markdown, render_table
from .schedule import (DEFAULT_WORK_END, DEFAULT_WORK_START, best_rows,
                       grid, parse_time, parse_zone)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="awakehours",
        description="Find the hours when your whole team is actually awake: "
                    "an hourly grid of who is inside working hours, ranked "
                    "by the least painful overlap.",
        epilog="examples:  awakehours America/Los_Angeles Europe/Berlin "
               "Asia/Shanghai  ·  awakehours ... --start 10:00 --duration 30",
    )
    p.add_argument("zones", nargs="+", metavar="ZONE",
                   help="IANA time zones, e.g. Asia/Shanghai (2+ recommended)")
    p.add_argument("--date", metavar="YYYY-MM-DD",
                   help="the day to plan (default: today, UTC)")
    p.add_argument("--duration", type=int, default=60, metavar="MIN",
                   help="meeting length in minutes (default 60)")
    p.add_argument("--start", default=DEFAULT_WORK_START, metavar="HH:MM",
                   help="working hours start (default 09:00)")
    p.add_argument("--end", default=DEFAULT_WORK_END, metavar="HH:MM",
                   help="working hours end (default 18:00)")
    p.add_argument("--top", type=int, default=3, metavar="N",
                   help="how many best slots to show (default 3)")
    p.add_argument("--json", dest="fmt", action="store_const", const="json",
                   help="machine-readable JSON output")
    p.add_argument("--markdown", "--md", dest="fmt", action="store_const",
                   const="markdown", help="markdown output for scheduling threads")
    p.add_argument("--version", action="version",
                   version=f"awakehours {__version__}")
    return p


def _parse_date(text: str | None) -> date:
    if not text:
        return datetime.now(timezone.utc).date()
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"expected YYYY-MM-DD, got {text!r}") from None


def main(argv=None) -> int:
    parser = build_parser()
    opts = parser.parse_args(argv)
    if opts.duration <= 0:
        parser.error("--duration must be positive")
    if opts.top < 1:
        parser.error("--top must be >= 1")

    try:
        zones = [parse_zone(name) for name in opts.zones]
        work_start = parse_time(opts.start)
        work_end = parse_time(opts.end)
        day = _parse_date(opts.date)
    except ValueError as e:
        print(f"awakehours: {e}", file=sys.stderr)
        return 1
    if work_end <= work_start:
        print("awakehours: --end must be after --start", file=sys.stderr)
        return 1

    rows = grid(day, zones, opts.duration, work_start, work_end)
    doc = {
        "date": day.isoformat(),
        "duration": opts.duration,
        "work": {"start": opts.start, "end": opts.end},
        "zones": [{"name": z.key, "label": z.key.rsplit("/", 1)[-1].replace("_", " ")}
                  for z in zones],
        "rows": [
            {
                "utc": f"{hour:02d}:00",
                "in_hours": sum(1 for z in row if z.ok),
                "total_pain": sum(z.pain for z in row),
                "zones": [
                    {
                        "zone": v.zone,
                        "label": v.label,
                        "local": _json_hm(v.local),
                        "local_dt": v.local,
                        "ok": v.ok,
                        "pain": v.pain,
                    }
                    for v in row
                ],
            }
            for hour, row in enumerate(rows)
        ],
    }
    doc["best"] = best_rows(rows, opts.top)
    renderer = {"table": render_table, "json": render_json,
                "markdown": render_markdown}[opts.fmt or "table"]
    print(renderer(doc, opts))
    return 0


def _json_hm(dt) -> str:
    return dt.strftime("%H:%M")


if __name__ == "__main__":
    sys.exit(main())
