import unittest
from datetime import date
from zoneinfo import ZoneInfo

from awakehours.schedule import (best_rows, grid, minutes_outside,
                                 parse_time, parse_zone, zone_label)


class TestParsing(unittest.TestCase):
    def test_parse_time(self):
        self.assertEqual(parse_time("9:00"), (9, 0))
        self.assertEqual(parse_time("18:30"), (18, 30))

    def test_parse_time_rejects_garbage(self):
        for bad in ("9", "25:00", "09:70", "now", ""):
            with self.assertRaises(ValueError):
                parse_time(bad)

    def test_parse_zone(self):
        self.assertEqual(parse_zone("UTC").key, "UTC")
        with self.assertRaises(ValueError) as ctx:
            parse_zone("Mars/Olympus")
        self.assertIn("IANA", str(ctx.exception))

    def test_zone_label(self):
        self.assertEqual(zone_label("America/Los_Angeles"), "Los Angeles")
        self.assertEqual(zone_label("UTC"), "UTC")


class TestPain(unittest.TestCase):
    def test_inside_is_zero(self):
        self.assertEqual(minutes_outside(10, 0, 60, (9, 0), (18, 0)), 0)

    def test_before_work_measures_from_meeting_start(self):
        # 08:00-09:00 meeting ends exactly at work start, still starts early
        self.assertEqual(minutes_outside(8, 0, 60, (9, 0), (18, 0)), 60)

    def test_after_work(self):
        self.assertEqual(minutes_outside(19, 0, 60, (9, 0), (18, 0)), 60)

    def test_overlapping_boundary(self):
        self.assertEqual(minutes_outside(8, 30, 60, (9, 0), (18, 0)), 30)

    def test_meeting_must_end_before_close(self):
        # starts 17:00, ends 18:00 — fine; 17:30 ends 18:30 — 30 min pain
        self.assertEqual(minutes_outside(17, 0, 60, (9, 0), (18, 0)), 0)
        self.assertEqual(minutes_outside(17, 30, 60, (9, 0), (18, 0)), 30)


class TestGrid(unittest.TestCase):
    def test_fixed_offset_zone(self):
        zones = [ZoneInfo("UTC"), ZoneInfo("Asia/Kolkata")]
        rows = grid(date(2026, 11, 24), zones, 60, (9, 0), (18, 0))
        kolkata_4am = rows[4][1]  # UTC 04:00 -> 09:30 in Kolkata
        self.assertEqual(kolkata_4am.local.strftime("%H:%M"), "09:30")
        self.assertTrue(kolkata_4am.ok)
        self.assertFalse(rows[3][1].ok)  # 08:30 local — 30 min early

    def test_dst_shifts_new_york(self):
        zones = [ZoneInfo("America/New_York")]
        winter = grid(date(2026, 1, 15), zones, 60, (9, 0), (18, 0))
        summer = grid(date(2026, 7, 15), zones, 60, (9, 0), (18, 0))
        self.assertTrue(winter[14][0].ok)  # UTC 14:00 -> 09:00 EST
        self.assertTrue(summer[13][0].ok)  # UTC 13:00 -> 09:00 EDT


class TestBest(unittest.TestCase):
    def _row(self, ok_count, pain):
        from awakehours.schedule import ZoneVerdict
        from datetime import datetime, timezone

        def z(ok, pain):
            return ZoneVerdict("UTC", "UTC",
                               datetime(2026, 11, 24, tzinfo=timezone.utc),
                               ok, pain)
        return [z(i < ok_count, pain if i >= ok_count else 0)
                for i in range(3)]

    def test_prefers_more_people_then_less_pain(self):
        rows = [self._row(1, 500), self._row(2, 400), self._row(2, 100)]
        self.assertEqual(best_rows(rows, 3)[:2], [2, 1])

    def test_tie_prefers_earliest(self):
        rows = [self._row(2, 100), self._row(2, 100)]
        self.assertEqual(best_rows(rows, 2)[0], 0)


if __name__ == "__main__":
    unittest.main()
