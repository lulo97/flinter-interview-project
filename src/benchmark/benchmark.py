import sys
import os
import time
import argparse
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_lib_method import csv_lib
from manual_method import manual
from pandas_method import pandas_method
from polars_method import polars_method


def run_module(module, filename, method_name):
    # Each module exposes getMetric(filename) -> (metrics, rows_length)
    start = time.perf_counter()
    metrics, rows_length = module.getMetric(filename)

    top_ctr = module.getTop10HighestCTR(metrics)
    top_cpa = module.getTop10LowestCPA(metrics)

    if hasattr(module, 'save_dicts_to_csv'):
        module.save_dicts_to_csv(top_ctr, "top10_ctr.csv")
        module.save_dicts_to_csv(top_cpa, "top10_cpa.csv")
    elif hasattr(module, 'save_df_to_csv'):
        module.save_df_to_csv(top_ctr, "top10_ctr.csv")
        module.save_df_to_csv(top_cpa, "top10_cpa.csv")
    else:
        raise AttributeError(f"Module {module.__name__} has no known save function")

    end = time.perf_counter()

    return end - start, rows_length


def main():
    csv_file = "ad_data_test.csv"

    if not os.path.isfile(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        sys.exit(1)

    modules = [
        (csv_lib, "csv_lib"),
        (manual, "manual"),
        (pandas_method, "pandas"),
        (polars_method, "polars"),
    ]

    print(f"Benchmarking with file: {csv_file}")
    print("-" * 50)

    results = {}
    for module, name in modules:
        try:
            elapsed, row_count = run_module(module, csv_file, name)
            results[name] = (elapsed, row_count)
            print(f"{name:>10} : {elapsed:.6f} sec  (rows: {row_count})")
        except Exception as e:
            print(f"{name:>10} : FAILED  ({e})")
            results[name] = (None, None)


if __name__ == "__main__":
# csv_lib : 2.928765 sec  (rows: 1000001)
# manual : 1.466388 sec  (rows: 1000001)
# pandas : 0.747996 sec  (rows: 1000001)
# polars : 0.084390 sec  (rows: 1000001)

    main()