"""Rendering: table (ANSI, NO_COLOR aware), JSON, Markdown."""

from __future__ import annotations

import json
import os
import sys

from . import __version__


def _ansi_enabled() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


class Ansi:
    def __init__(self, enabled: bool = None):
        self.on = _ansi_enabled() if enabled is None else enabled

    def _wrap(self, code: int, s: str) -> str:
        return f"\x1b[{code}m{s}\x1b[0m" if self.on else s

    def bold(self, s): return self._wrap(1, s)
    def dim(self, s): return self._wrap(2, s)
    def red(self, s): return self._wrap(31, s)
    def green(self, s): return self._wrap(32, s)
    def yellow(self, s): return self._wrap(33, s)
    def cyan(self, s): return self._wrap(36, s)

    def mark(self, ok: bool) -> str:
        return self.green("✓") if ok else self.red("✗")


def _hm(dt) -> str:
    return dt.strftime("%H:%M")


def _weekday(dt) -> str:
    return dt.strftime("%a")


def render_table(res, opts) -> str:
    a = Ansi()
    out = []
    n = len(res["zones"])
    out.append(a.bold(f"awakehours v{__version__}")
               + a.dim(f"  ·  {res['date']}  ·  {res['duration']} min meeting"
                       f"  ·  work {res['work']['start']}–{res['work']['end']}"))
    out.append("")
    header = f"  {'UTC':>5}  " + "  ".join(f"{z['label']:>15}" for z in res["zones"])
    out.append(a.cyan(header))
    for row in res["rows"]:
        cells = []
        for verdict in row["zones"]:
            cells.append(f"{_hm(verdict['local_dt'])} "
                         f"{_weekday(verdict['local_dt'])[:2]} {a.mark(verdict['ok'])}"
                         .rjust(15))
        good = f"{row['in_hours']}/{n}"
        paint = a.green if row["in_hours"] == n else (a.yellow if row["in_hours"] else a.dim)
        out.append(f"  {row['utc']:>5}  " + "  ".join(cells)
                   + a.dim("   ") + paint(good))
    out.append("")

    best = res["best"]
    if not best:
        out.append(a.dim("(no rows)"))
        return "\n".join(out)
    if res["rows"][best[0]]["in_hours"] == n:
        slots = ", ".join(f"{res['rows'][i]['utc']} UTC" for i in best
                          if res["rows"][i]["in_hours"] == n)
        out.append(a.green(f"Everyone is awake at: {slots}"))
        return "\n".join(out)

    out.append(a.cyan("Best compromises (most people awake, then least pain)"))
    for rank, i in enumerate(best, 1):
        row = res["rows"][i]
        cells = " · ".join(
            f"{z['label']} {_hm(z['local_dt'])} {a.mark(z['ok'])}"
            for z in row["zones"]
        )
        out.append(f"  {rank}. {row['utc']} UTC  {cells}"
                   + a.dim(f"   ({row['in_hours']}/{n} awake,"
                           f" pain {row['total_pain']} min)"))
    return "\n".join(out)


def render_json(res, opts) -> str:
    doc = dict(res)
    doc["rows"] = [
        {**row, "zones": [
            {k: v for k, v in z.items() if k != "local_dt"}
            for z in row["zones"]
        ]}
        for row in res["rows"]
    ]
    doc["tool"] = "awakehours"
    doc["version"] = __version__
    return json.dumps(doc, indent=2, ensure_ascii=False, default=str)


def render_markdown(res, opts) -> str:
    n = len(res["zones"])
    lines = [
        f"## awakehours — {res['date']}, {res['duration']} min",
        "",
        "| UTC | " + " | ".join(z["label"] for z in res["zones"]) + " | awake |",
        "|---:|" + "---|" * n + "---:|",
    ]
    for row in res["rows"]:
        cells = " | ".join(
            f"{_hm(z['local_dt'])} {_weekday(z['local_dt'])[:2]} "
            f"{'✓' if z['ok'] else '✗'}" for z in row["zones"]
        )
        lines.append(f"| {row['utc']} | {cells} | {row['in_hours']}/{n} |")
    best = res["best"]
    if res["rows"][best[0]]["in_hours"] == n:
        slots = ", ".join(f"{res['rows'][i]['utc']} UTC" for i in best
                          if res["rows"][i]["in_hours"] == n)
        lines += ["", f"**Everyone is awake at: {slots}**"]
    else:
        lines += ["", "**Best compromises:**"]
        for rank, i in enumerate(best, 1):
            row = res["rows"][i]
            cells = " · ".join(
                f"{z['label']} {_hm(z['local_dt'])} {'✓' if z['ok'] else '✗'}"
                for z in row["zones"]
            )
            lines.append(f"{rank}. {row['utc']} UTC — {cells}"
                         f" ({row['in_hours']}/{n} awake)")
    return "\n".join(lines)
