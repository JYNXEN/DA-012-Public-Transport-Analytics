"""Regression checks for the source workbook extraction."""
import unittest
from pathlib import Path

from src.ridership_analysis import load_ridership_data, build_summary_tables

ROOT = Path(__file__).resolve().parents[1]


class RidershipExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_ridership_data(ROOT / "data")
        cls.tables = build_summary_tables(cls.data)

    def test_expected_routes_and_periods_are_present(self):
        self.assertEqual(set(self.data["route"].unique()), {"C1 Blue", "C1 Gold", "C2 Express", "G-Line"})
        self.assertEqual(set(self.data["period"].unique()), {"October 2018", "February 2019"})

    def test_route_totals_match_source_workbook_totals(self):
        expected = {
            ("October 2018", "C1 Blue"): 5976,
            ("October 2018", "C1 Gold"): 5829,
            ("October 2018", "C2 Express"): 13552,
            ("October 2018", "G-Line"): 5261,
            ("February 2019", "C1 Blue"): 4304,
            ("February 2019", "C1 Gold"): 4005,
            ("February 2019", "C2 Express"): 12053,
            ("February 2019", "G-Line"): 6299,
        }
        actual = {
            (row.period, row.route): row.total_boardings
            for row in self.tables["route_summary"].itertuples(index=False)
        }
        self.assertEqual(actual, expected)

    def test_no_negative_or_missing_passenger_counts(self):
        self.assertFalse(self.data["passenger_count"].isna().any())
        self.assertTrue((self.data["passenger_count"] > 0).all())


if __name__ == "__main__":
    unittest.main()
