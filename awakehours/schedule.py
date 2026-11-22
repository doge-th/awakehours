"""The hourly grid: who is inside working hours at every UTC slot."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_WORK_START = "09:00"
DEFAULT_WORK_END = "18:00"


@dataclass
class ZoneVerdict:
    zone: str  # e.g. "Asia/Kolkata"
    label: str  # short column label, e.g. "Kolkata"
    local: datetime  # local wall clock at the slot's start
    ok: bool  # meeting starts inside working hours
    pain: int  # minutes from the nearest working-hours boundary if outside


def parse_time(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text.strip())
    if not m or not (0 <= int(m.group(1)) <= 23 and 0 <= int(m.group(2)) <= 59):
        raise ValueError(f"expected HH:MM (24h), got {text!r}")
    return int(m.group(1)), int(m.group(2))


def parse_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        raise ValueError(
            f"unknown time zone {name!r} — use IANA names like "
            f"'Asia/Shanghai' or 'America/Los_Angeles'; on Windows you may "
            f"need: pip install tzdata"
        ) from None


def zone_label(name: str) -> str:
    return name.rsplit("/", 1)[-1].replace("_", " ")


def minutes_outside(local_hour: int, local_minute: int, duration: int,
                    start: tuple[int, int], end: tuple[int, int]) -> int:
    """Minutes of the meeting that fall outside working hours (0 if all in).

    Working hours are [start, end); a meeting fits when it starts at or
    after *start* and ends at or before *end* — pain == 0 exactly then.
    """
    begin = local_hour * 60 + local_minute
    finish = begin + duration
    ws, we = start[0] * 60 + start[1], end[0] * 60 + end[1]
    overlap = max(0, min(finish, we) - max(begin, ws))
    return duration - overlap


def grid(day: date, zones: list[ZoneInfo], duration: int,
         work_start: tuple[int, int], work_end: tuple[int, int]) -> list[list[ZoneVerdict]]:
    """For every UTC hour of *day*, the verdict in each zone."""
    rows = []
    for hour in range(24):
        instant = datetime(day.year, day.month, day.day, hour,
                           tzinfo=timezone.utc)
        row = []
        for zone in zones:
            local = instant.astimezone(zone)
            pain = minutes_outside(local.hour, local.minute, duration,
                                   work_start, work_end)
            row.append(ZoneVerdict(
                zone=zone.key, label=zone_label(zone.key), local=local,
                ok=pain == 0, pain=pain,
            ))
        rows.append(row)
    return rows


def score_row(row: list[ZoneVerdict]) -> tuple[int, int]:
    """(zones in hours desc, total pain asc) — sort key, lower is better."""
    return (-sum(1 for z in row if z.ok), sum(z.pain for z in row))


def best_rows(rows: list[list[ZoneVerdict]], limit: int = 3) -> list[int]:
    """Indices of the most livable slots, earliest first on ties."""
    return sorted(range(len(rows)), key=lambda i: (*score_row(rows[i]), i))[:limit]
