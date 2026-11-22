# awakehours 🌍

[![CI](https://img.shields.io/github/actions/workflow/status/doge-th/awakehours/ci.yml?branch=main&label=CI)](https://github.com/doge-th/awakehours/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

**Find the hours when your whole team is actually awake.**

An hourly grid of who is inside working hours across time zones — DST-aware,
zero dependencies — plus a ranked list of the least painful compromises when
no perfect slot exists (spoiler: across 9+ hours, there never is).

```
$ awakehours --date 2026-11-24 America/Los_Angeles Europe/Berlin Asia/Kolkata

awakehours v0.1.0  ·  2026-11-24  ·  60 min meeting  ·  work 09:00–18:00

    UTC      Los Angeles           Berlin          Kolkata
  00:00       16:00 Mo ✓       01:00 Tu ✗       05:30 Tu ✗   1/3
  01:00       17:00 Mo ✓       02:00 Tu ✗       06:30 Tu ✗   1/3
  ...
  08:00       00:00 Tu ✗       09:00 Tu ✓       13:30 Tu ✓   2/3
  09:00       01:00 Tu ✗       10:00 Tu ✓       14:30 Tu ✓   2/3
  ...
  17:00       09:00 Tu ✓       18:00 Tu ✗       22:30 Tu ✗   2/3
  ...

Best compromises (most people awake, then least pain)
  1. 08:00 UTC  Los Angeles 00:00 ✗ · Berlin 09:00 ✓ · Kolkata 13:30 ✓   (2/3 awake, pain 60 min)
  2. 09:00 UTC  Los Angeles 01:00 ✗ · Berlin 10:00 ✓ · Kolkata 14:30 ✓   (2/3 awake, pain 60 min)
  3. 10:00 UTC  Los Angeles 02:00 ✗ · Berlin 11:00 ✓ · Kolkata 15:30 ✓   (2/3 awake, pain 60 min)
```

*(real output — trimmed midday rows for brevity. Los Angeles, Berlin and
Kolkata share no waking window at all: the grid shows exactly who pays at
every hour, and the ranking picks the smallest sacrifice.)*

## What you get

- **The grid** — every UTC hour with the local wall-clock time in each zone,
  a ✓/✗ for working hours, and how many zones are awake.
- **Best compromises** — ranked by (1) most people inside working hours,
  (2) fewest total minutes spent outside them, (3) earliest UTC hour.
  When everyone can't be awake, it tells you *who* is paying.
- Weekday letters (`Mo`/`Tu`) reveal day flips at a glance.
- DST handled by `zoneinfo` — the same command gives different answers in
  January and July, correctly.

## Install

```bash
pip install git+https://github.com/doge-th/awakehours.git
# or without touching your environment:
pipx install git+https://github.com/doge-th/awakehours.git
uvx --from git+https://github.com/doge-th/awakehours.git awakehours ...
```

On Windows, Python's `zoneinfo` needs the tz database as a package:
`pip install tzdata`.

## Usage

```bash
awakehours America/Los_Angeles Europe/Berlin Asia/Shanghai
awakehours --date 2026-12-01 --duration 30 --start 10:00 --end 17:00 ...
awakehours ... --top 5        # more compromise options
awakehours ... --json         # the full grid, machine-readable
awakehours ... --markdown     # paste-ready table for the scheduling thread
```

`--json` contains every row (local times, ok/pain per zone, `in_hours`,
`total_pain`) plus the ranked `best` indices:

```bash
awakehours UTC Asia/Kolkata --json | jq '.best[0]'
```

## Method (and its honest limits)

- One row per UTC hour of the chosen day; a meeting *fits* a zone when it
  starts at/after the work window opens **and** ends at/before it closes.
  `pain` is the number of meeting minutes that fall outside — so a meeting
  straddling the 18:00 boundary hurts exactly as much as it overruns.
- Ranking: most zones awake, then least total pain, then earliest UTC.
  Ties resolve deterministically, so the same command always shows the same
  answer.
- Hourly granularity only: an 09:30 local start shows as a 09:00 slot.
  Half-hour zones (India, Iran, …) display correctly; only the grid steps by
  the hour.

## 中文说明

**awakehours:算出"全团队都醒着"的时间段。** 每个 UTC 小时一行,列出各地
的本地时间、是否在 9-18 点工作时间内,没有完美时段时(隔着 9 小时以上
从来不可能有),按"醒着的人最多 → 总痛苦分钟数最少 → UTC 最早"给出最不
难受的折中方案——并且明说是谁在付半夜。DST 由 zoneinfo 处理,夏令时切换
自动正确;零依赖,离线可用。Windows 上需要 `pip install tzdata`。

```bash
pip install git+https://github.com/doge-th/awakehours.git
awakehours America/Los_Angeles Europe/Berlin Asia/Shanghai
awakehours ... --markdown      # 贴进排会邮件线程
```

配套工具:[toktree](https://github.com/doge-th/toktree)(上下文窗口预算)、
[githotspot](https://github.com/doge-th/githotspot)(churn × 复杂度热点)、
[todomold](https://github.com/doge-th/todomold)(TODO 腐烂排行)。

## Related tools

- [csvpulse](https://github.com/doge-th/csvpulse) — take the pulse of a CSV file in one command
- [toktree](https://github.com/doge-th/toktree) — `du` for your LLM context window
- [githotspot](https://github.com/doge-th/githotspot) — churn × complexity hotspots in your git history
- [todomold](https://github.com/doge-th/todomold) — your oldest TODOs, with who wrote them and how long they've rotted

## Development

```bash
python -m unittest discover -s tests   # zero-dep suite, DST tests included
```

## License

[MIT](LICENSE) © 2026 doge-th
