import contextlib
import io
import json
import unittest

from awakehours import __version__
from awakehours.cli import main


class TestCli(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_table_report(self):
        code, out, _ = self._run(
            ["--date", "2026-11-24", "UTC", "Asia/Kolkata"]
        )
        self.assertEqual(code, 0)
        self.assertIn("UTC", out)
        self.assertIn("Kolkata", out)
        self.assertIn("2026-11-24", out)

    def test_json_report(self):
        _, out, _ = self._run(["--json", "--date", "2026-11-24",
                               "UTC", "Asia/Kolkata"])
        doc = json.loads(out)
        self.assertEqual(doc["tool"], "awakehours")
        self.assertEqual(doc["version"], __version__)
        self.assertEqual(len(doc["rows"]), 24)
        # UTC 04:00 is 09:30 in Kolkata on any day of the year
        row4 = doc["rows"][4]
        self.assertEqual(row4["zones"][1]["local"], "09:30")
        self.assertTrue(row4["zones"][1]["ok"])

    def test_markdown_report(self):
        _, out, _ = self._run(["--markdown", "--date", "2026-11-24",
                               "UTC", "Asia/Kolkata"])
        self.assertIn("## awakehours — 2026-11-24, 60 min", out)

    def test_unknown_zone_fails_with_hint(self):
        code, _, err = self._run(["Mars/Olympus", "UTC"])
        self.assertEqual(code, 1)
        self.assertIn("IANA", err)

    def test_bad_date_fails(self):
        code, _, err = self._run(["--date", "tomorrow", "UTC", "UTC"])
        self.assertEqual(code, 1)
        self.assertIn("YYYY-MM-DD", err)

    def test_end_before_start_fails(self):
        code, _, err = self._run(["--start", "18:00", "--end", "09:00",
                                  "UTC", "UTC"])
        self.assertEqual(code, 1)
        self.assertIn("--end must be after --start", err)

    def test_zero_duration_rejected(self):
        with self.assertRaises(SystemExit):
            main(["--duration", "0", "UTC", "UTC"])

    def test_version_flag(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
