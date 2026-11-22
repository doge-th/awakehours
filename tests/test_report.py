import contextlib
import io
import json
import unittest

from awakehours import __version__
from awakehours.cli import main


def _doc(**overrides):
    from datetime import datetime, timezone

    local_dt = datetime(2026, 11, 24, 9, 30, tzinfo=timezone.utc)

    def zone(ok, pain):
        return {"zone": "Asia/Kolkata", "label": "Kolkata",
                "local": "09:30", "local_dt": local_dt,
                "ok": ok, "pain": pain}

    res = {
        "date": "2026-11-24",
        "duration": 60,
        "work": {"start": "09:00", "end": "18:00"},
        "zones": [{"name": "Asia/Kolkata", "label": "Kolkata"}],
        "rows": [
            {"utc": "04:00", "in_hours": 1, "total_pain": 0,
             "zones": [zone(True, 0)]}
        ],
        "best": [0],
    }
    res.update(overrides)
    return res


class _Opts:
    top = 3


class TestRenderers(unittest.TestCase):
    def test_table_perfect_row(self):
        from awakehours.report import render_table
        out = render_table(_doc(), _Opts)
        self.assertIn("Everyone is awake at: 04:00 UTC", out)
        self.assertIn("Kolkata", out)
        self.assertIn("2026-11-24", out)

    def test_table_best_compromises(self):
        from awakehours.report import render_table
        res = _doc()
        res["rows"][0]["in_hours"] = 0
        res["rows"][0]["zones"][0]["ok"] = False
        out = render_table(res, _Opts)
        self.assertIn("Best compromises", out)
        self.assertIn("0/1 awake", out)

    def test_json_has_no_datetime(self):
        from awakehours.report import render_json
        doc = json.loads(render_json(_doc(), _Opts))
        self.assertEqual(doc["tool"], "awakehours")
        self.assertEqual(doc["version"], __version__)
        self.assertNotIn("local_dt", doc["rows"][0]["zones"][0])
        self.assertEqual(doc["rows"][0]["zones"][0]["local"], "09:30")

    def test_markdown_grid(self):
        from awakehours.report import render_markdown
        out = render_markdown(_doc(), _Opts)
        self.assertIn("## awakehours — 2026-11-24, 60 min", out)
        self.assertIn("| UTC | Kolkata | awake |", out)


if __name__ == "__main__":
    unittest.main()
