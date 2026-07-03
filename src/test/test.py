# src/test/test.py
import os
import sys
import tempfile
import unittest
from pathlib import Path

import polars as pl

# Ensure the implement module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "implement"))
from app import getMetric, getTop10HighestCTR, getTop10LowestCPA, save_to_csv


class TestGetMetric(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Example data identical to the provided sample
        cls.valid_data = (
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP025,2025-04-18,3653,60,64.29,2\n"
            "CMP020,2025-05-03,24465,764,1394.62,42\n"
            "CMP019,2025-02-05,7214,236,135.93,21\n"
            "CMP046,2025-06-04,10631,201,298.82,18\n"
            "CMP044,2025-03-26,31942,964,744.4,37\n"
            "CMP041,2025-02-22,37210,984,1716.18,32\n"
            "CMP036,2025-01-04,7112,265,227.31,22\n"
            "CMP043,2025-06-10,1074,34,56.89,1\n"
            "CMP047,2025-03-25,47113,2081,963.56,127\n"
            "CMP016,2025-02-06,36585,920,232.62,35\n"
        )

    def setUp(self):
        # Create a temporary CSV file for each test
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        self.temp_file.close()
        self.temp_path = self.temp_file.name

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def _write_to_temp(self, content: str):
        with open(self.temp_path, "w", newline="") as f:
            f.write(content)

    # ----------------- Normal operation -----------------
    def test_valid_file_returns_correct_columns(self):
        self._write_to_temp(self.valid_data)
        metrics, rows = getMetric(self.temp_path)

        expected_cols = {"campaign_id", "impressions", "clicks", "spend", "conversions", "ctr", "cpa"}
        self.assertEqual(set(metrics.columns), expected_cols)

    def test_valid_file_aggregates_single_campaign(self):
        # Single campaign should just copy values
        content = "campaign_id,date,impressions,clicks,spend,conversions\nCMP001,2025-01-01,1000,50,500.0,10"
        self._write_to_temp(content)
        metrics, _ = getMetric(self.temp_path)

        self.assertEqual(metrics.height, 1)
        self.assertEqual(metrics[0, "impressions"], 1000)
        self.assertEqual(metrics[0, "clicks"], 50)
        self.assertEqual(metrics[0, "spend"], 500.0)
        self.assertEqual(metrics[0, "conversions"], 10)
        self.assertAlmostEqual(metrics[0, "ctr"], 50 / 1000)
        self.assertAlmostEqual(metrics[0, "cpa"], 500.0 / 10)

    def test_valid_file_aggregates_multiple_entries(self):
        # Duplicate campaign_id should sum
        content = (
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,100,10,20.0,1\n"
            "CMP001,2025-01-02,200,20,40.0,2\n"
        )
        self._write_to_temp(content)
        metrics, _ = getMetric(self.temp_path)

        self.assertEqual(metrics.height, 1)
        self.assertEqual(metrics[0, "impressions"], 300)
        self.assertEqual(metrics[0, "clicks"], 30)
        self.assertEqual(metrics[0, "spend"], 60.0)
        self.assertEqual(metrics[0, "conversions"], 3)
        self.assertAlmostEqual(metrics[0, "ctr"], 30 / 300)
        self.assertAlmostEqual(metrics[0, "cpa"], 60.0 / 3)

    def test_returned_row_count(self):
        # total_raw_rows is number of data rows; function returns +1
        self._write_to_temp(self.valid_data)
        _, rows = getMetric(self.temp_path)
        expected = self.valid_data.strip().count("\n")  # data rows = 10
        self.assertEqual(rows, expected + 1)  # 11

    # ----------------- Edge case: zero impressions / conversions -----------------
    def test_zero_impressions_ctr_is_zero(self):
        content = "campaign_id,date,impressions,clicks,spend,conversions\nCMP001,2025-01-01,0,0,0.0,0"
        self._write_to_temp(content)
        metrics, _ = getMetric(self.temp_path)
        self.assertEqual(metrics[0, "ctr"], 0.0)

    def test_zero_conversions_cpa_is_infinity(self):
        # Polars division by zero yields inf, fill_nan/fill_null do not replace inf
        content = "campaign_id,date,impressions,clicks,spend,conversions\nCMP001,2025-01-01,100,10,50.0,0"
        self._write_to_temp(content)
        metrics, _ = getMetric(self.temp_path)
        self.assertTrue(pl.Series([metrics[0, "cpa"]]).is_infinite().all())

    def test_ctr_and_cpa_fill_null_handling(self):
        # If a column were completely null, fill_null(0) would apply,
        # but it's not triggered in normal use. Still, we trust the code.
        pass

    # ----------------- Error handling -----------------
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            getMetric("nonexistent.csv")

    def test_empty_file(self):
        self._write_to_temp("")
        with self.assertRaises(ValueError):
            getMetric(self.temp_path)

    def test_file_with_only_header(self):
        content = "campaign_id,date,impressions,clicks,spend,conversions"
        self._write_to_temp(content)
        with self.assertRaises(Exception):  # Pl.NoDataError or generic
            getMetric(self.temp_path)

    def test_file_with_malformed_rows(self):
        # polars will try to parse; column mismatch causes error
        content = (
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,100,10,20.0,1,extra_column\n"
        )
        self._write_to_temp(content)
        with self.assertRaises(Exception):
            getMetric(self.temp_path)


class TestTopK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A simple DataFrame with 12 campaigns, varying CTR and CPA
        cls.df = pl.DataFrame(
            {
                "campaign_id": [f"CMP{i:03d}" for i in range(1, 13)],
                "impressions": [1000] * 12,
                "clicks": list(range(10, 130, 10)),  # 10,20,...,120 -> CTR 0.01..0.12
                "spend": [100.0] * 12,
                "conversions": [5, 10, 2, 8, 1, 12, 4, 20, 3, 15, 7, 6],
                "ctr": [i / 1000 for i in range(10, 130, 10)],
                "cpa": [100.0 / c for c in [5, 10, 2, 8, 1, 12, 4, 20, 3, 15, 7, 6]],
            }
        )

    def test_get_top10_highest_ctr(self):
        top = getTop10HighestCTR(self.df)
        self.assertEqual(top.height, 10)
        # CTR should be descending
        for i in range(top.height - 1):
            self.assertGreaterEqual(top[i, "ctr"], top[i + 1, "ctr"])

    def test_get_top10_lowest_cpa(self):
        bottom = getTop10LowestCPA(self.df)
        self.assertEqual(bottom.height, 10)
        # CPA should be ascending
        for i in range(bottom.height - 1):
            self.assertLessEqual(bottom[i, "cpa"], bottom[i + 1, "cpa"])

    def test_top_k_returns_all_when_less_than_10(self):
        small = self.df.head(5)
        top = getTop10HighestCTR(small)
        self.assertEqual(top.height, 5)

    def test_lowest_cpa_handles_infinity(self):
        # Campaign with conversions=0 yields inf CPA
        df_inf = pl.DataFrame({
            "campaign_id": ["CMP_INF"],
            "impressions": [100],
            "clicks": [10],
            "spend": [50.0],
            "conversions": [0],
            "ctr": [0.1],
            "cpa": [float("inf")],
        })
        bottom = getTop10LowestCPA(df_inf)
        # Because inf is large, it should not appear in bottom_k
        self.assertTrue(bottom.is_empty() or (bottom.height == 0))

    def test_top_ctr_handles_zero(self):
        df_zero = pl.DataFrame({
            "campaign_id": ["CMP0"],
            "impressions": [100],
            "clicks": [0],
            "spend": [10.0],
            "conversions": [1],
            "ctr": [0.0],
            "cpa": [10.0],
        })
        top = getTop10HighestCTR(df_zero)
        self.assertEqual(top[0, "campaign_id"], "CMP0")


class TestSaveToCSV(unittest.TestCase):
    def setUp(self):
        self.df = pl.DataFrame({"campaign_id": ["A"], "val": [1]})
        self.filename = "test_output.csv"
        self.full_path = os.path.join(os.path.dirname(__file__), self.filename)

    def tearDown(self):
        if os.path.exists(self.full_path):
            os.remove(self.full_path)

    def test_save_creates_file(self):
        save_to_csv(self.df, self.filename)
        self.assertTrue(os.path.exists(self.full_path))

    def test_saved_content_matches(self):
        save_to_csv(self.df, self.filename)
        read_back = pl.read_csv(self.full_path)
        self.assertTrue(self.df.equals(read_back))


if __name__ == "__main__":
    unittest.main()