# src/test/test.py

import os
import sys
import tempfile
import unittest
from pathlib import Path

import polars as pl

# Ensure the implement module can be imported
IMPLEMENT_DIR = Path(__file__).resolve().parent.parent / "implement"
sys.path.insert(0, str(IMPLEMENT_DIR))

import app
from app import (
    getMetric,
    getTop10HighestCTR,
    getTop10LowestCPA,
    save_to_csv,
)


class TestGetMetric(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_data = (
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP025,2025-04-18,3653,60,64.29,2\n"
            "CMP020,2025-05-03,24465,764,1394.62,42\n"
            "CMP019,2025-02-05,7214,236,135.93,21\n"
            "CMP046,2025-06-04,10631,201,298.82,18\n"
            "CMP044,2025-03-26,31942,964,744.40,37\n"
            "CMP041,2025-02-22,37210,984,1716.18,32\n"
            "CMP036,2025-01-04,7112,265,227.31,22\n"
            "CMP043,2025-06-10,1074,34,56.89,1\n"
            "CMP047,2025-03-25,47113,2081,963.56,127\n"
            "CMP016,2025-02-06,36585,920,232.62,35\n"
        )

    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        tmp.close()
        self.temp_path = tmp.name

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def _write(self, text: str):
        with open(self.temp_path, "w", newline="") as f:
            f.write(text)

    # ---------------- Normal cases ----------------

    def test_valid_file_returns_correct_columns(self):
        self._write(self.valid_data)

        metrics, rows = getMetric(self.temp_path)

        self.assertEqual(rows, 11)

        expected = {
            "campaign_id",
            "impressions",
            "clicks",
            "spend",
            "conversions",
            "ctr",
            "cpa",
        }

        self.assertEqual(set(metrics.columns), expected)

    def test_single_campaign(self):
        self._write(
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,1000,50,500.0,10\n"
        )

        metrics, _ = getMetric(self.temp_path)

        self.assertEqual(metrics.height, 1)
        self.assertEqual(metrics[0, "campaign_id"], "CMP001")
        self.assertEqual(metrics[0, "impressions"], 1000)
        self.assertEqual(metrics[0, "clicks"], 50)
        self.assertEqual(metrics[0, "spend"], 500.0)
        self.assertEqual(metrics[0, "conversions"], 10)
        self.assertAlmostEqual(metrics[0, "ctr"], 0.05)
        self.assertAlmostEqual(metrics[0, "cpa"], 50.0)

    def test_multiple_rows_same_campaign(self):
        self._write(
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,100,10,20.0,1\n"
            "CMP001,2025-01-02,200,20,40.0,2\n"
        )

        metrics, _ = getMetric(self.temp_path)

        self.assertEqual(metrics.height, 1)
        self.assertEqual(metrics[0, "impressions"], 300)
        self.assertEqual(metrics[0, "clicks"], 30)
        self.assertEqual(metrics[0, "spend"], 60.0)
        self.assertEqual(metrics[0, "conversions"], 3)
        self.assertAlmostEqual(metrics[0, "ctr"], 0.1)
        self.assertAlmostEqual(metrics[0, "cpa"], 20.0)

    def test_returned_row_count(self):
        self._write(self.valid_data)

        _, rows = getMetric(self.temp_path)

        self.assertEqual(rows, 11)

    # ---------------- Edge cases ----------------

    def test_zero_impressions_ctr(self):
        self._write(
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,0,0,0.0,0\n"
        )

        metrics, _ = getMetric(self.temp_path)

        self.assertEqual(metrics[0, "ctr"], 0.0)

    def test_zero_conversions_cpa_is_inf(self):
        self._write(
            "campaign_id,date,impressions,clicks,spend,conversions\n"
            "CMP001,2025-01-01,100,10,50.0,0\n"
        )

        metrics, _ = getMetric(self.temp_path)

        self.assertTrue(
            pl.Series([metrics[0, "cpa"]]).is_infinite().all()
        )

    # ---------------- Error cases ----------------

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            getMetric("missing.csv")

    def test_empty_file(self):
        self._write("")

        with self.assertRaises(ValueError):
            getMetric(self.temp_path)

    def test_header_only(self):
        self._write(
            "campaign_id,date,impressions,clicks,spend,conversions\n"
        )

        with self.assertRaises(Exception):
            getMetric(self.temp_path)

class TestTopK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pl.DataFrame(
            {
                "campaign_id": [f"CMP{i:03d}" for i in range(1, 13)],
                "impressions": [1000] * 12,
                "clicks": list(range(10, 130, 10)),
                "spend": [100.0] * 12,
                "conversions": [5, 10, 2, 8, 1, 12, 4, 20, 3, 15, 7, 6],
                "ctr": [i / 1000 for i in range(10, 130, 10)],
                "cpa": [
                    100.0 / c
                    for c in [5, 10, 2, 8, 1, 12, 4, 20, 3, 15, 7, 6]
                ],
            }
        )

    def test_get_top10_highest_ctr(self):
        top = getTop10HighestCTR(self.df)

        self.assertEqual(top.height, 10)

        ctrs = top["ctr"].to_list()

        for i in range(len(ctrs) - 1):
            self.assertGreaterEqual(ctrs[i], ctrs[i + 1])

    def test_get_top10_lowest_cpa(self):
        bottom = getTop10LowestCPA(self.df)

        self.assertEqual(bottom.height, 10)

        cpas = bottom["cpa"].to_list()

        for i in range(len(cpas) - 1):
            self.assertLessEqual(cpas[i], cpas[i + 1])

    def test_top_k_less_than_10(self):
        small = self.df.head(5)

        top = getTop10HighestCTR(small)

        self.assertEqual(top.height, 5)

    def test_bottom_k_single_inf(self):
        df = pl.DataFrame(
            {
                "campaign_id": ["CMP_INF"],
                "impressions": [100],
                "clicks": [10],
                "spend": [50.0],
                "conversions": [0],
                "ctr": [0.1],
                "cpa": [float("inf")],
            }
        )

        result = getTop10LowestCPA(df)

        self.assertEqual(result.height, 1)
        self.assertTrue(
            pl.Series([result[0, "cpa"]]).is_infinite().all()
        )

    def test_top_ctr_zero(self):
        df = pl.DataFrame(
            {
                "campaign_id": ["CMP0"],
                "impressions": [100],
                "clicks": [0],
                "spend": [10.0],
                "conversions": [1],
                "ctr": [0.0],
                "cpa": [10.0],
            }
        )

        top = getTop10HighestCTR(df)

        self.assertEqual(top.height, 1)
        self.assertEqual(top[0, "campaign_id"], "CMP0")


class TestSaveToCSV(unittest.TestCase):
    def setUp(self):
        self.df = pl.DataFrame(
            {
                "campaign_id": ["CMP001"],
                "impressions": [100],
                "clicks": [10],
                "spend": [25.5],
                "conversions": [5],
                "ctr": [0.1],
                "cpa": [5.1],
            }
        )

        self.filename = "test_output.csv"

        self.output_path = os.path.join(
            os.path.dirname(os.path.abspath(app.__file__)),
            self.filename,
        )

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_save_creates_file(self):
        save_to_csv(self.df, self.filename)

        self.assertTrue(os.path.exists(self.output_path))

    def test_saved_columns(self):
        save_to_csv(self.df, self.filename)

        saved = pl.read_csv(self.output_path)

        self.assertEqual(
            saved.columns,
            [
                "campaign_id",
                "total_impressions",
                "total_clicks",
                "total_spend",
                "total_conversions",
                "CTR",
                "CPA",
            ],
        )

    def test_saved_values(self):
        save_to_csv(self.df, self.filename)

        saved = pl.read_csv(self.output_path)

        self.assertEqual(saved[0, "campaign_id"], "CMP001")
        self.assertEqual(saved[0, "total_impressions"], 100)
        self.assertEqual(saved[0, "total_clicks"], 10)
        self.assertEqual(saved[0, "total_conversions"], 5)
        self.assertAlmostEqual(saved[0, "total_spend"], 25.5)
        self.assertAlmostEqual(saved[0, "CTR"], 0.1)
        self.assertAlmostEqual(saved[0, "CPA"], 5.1)


if __name__ == "__main__":
    unittest.main()