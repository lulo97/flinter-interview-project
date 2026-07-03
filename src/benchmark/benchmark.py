import sys
import os
from threading import Thread
import threading
import time
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_lib_method import csv_lib
from manual_method import manual
from pandas_method import pandas_method
from polars_method import polars_method
from pyarrow_method import pyarrow_method
from implement import app

process = psutil.Process(os.getpid())

def run_module(module, filename):
    stop_event = threading.Event()
    
    uss_monitor_list = [process.memory_full_info().uss]

    main_thread_id = threading.get_native_id()

    def monitor_memory():
        monitor_thread_id = threading.get_native_id()
        print(f"Main thread: {main_thread_id} | Monitor thread: {monitor_thread_id}")

        while not stop_event.is_set():
            current_uss = process.memory_full_info().uss
            uss_monitor_list.append(current_uss)
            time.sleep(0.005)

    monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
    monitor_thread.start()

    time_deltas = {}
    t0_time = time.perf_counter()

    metrics, rows_length = module.getMetric(filename)
    t1_time = time.perf_counter()
    
    time_deltas['getMetric'] = t1_time - t0_time

    top_ctr = module.getTop10HighestCTR(metrics)
    t2_time = time.perf_counter()
    
    time_deltas['get_top_ctr'] = t2_time - t1_time

    top_cpa = module.getTop10LowestCPA(metrics)
    t3_time = time.perf_counter()
    
    time_deltas['get_top_cpa'] = t3_time - t2_time

    if hasattr(module, 'save_to_csv'):
        # Save CTR
        module.save_to_csv(top_ctr, "top10_ctr.csv")
        t4_time = time.perf_counter()
        time_deltas['save_top_ctr'] = t4_time - t3_time
        
        # Save CPA
        module.save_to_csv(top_cpa, "top10_cpa.csv")
        t5_time = time.perf_counter()
        time_deltas['save_top_cpa'] = t5_time - t4_time

    time_deltas['net_total'] = t5_time - t0_time

    stop_event.set()
    monitor_thread.join()

    return time_deltas, uss_monitor_list, rows_length

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
        (pyarrow_method, "pyarrow"),
        (app, "implement")
    ]

    print(f"Benchmarking with file: {csv_file}")
    print("-" * 50)

    results = {}
    for module, name in modules:
        time_deltas, uss_history, rows_length = run_module(module, csv_file)
        
        results[name] = {
            "time": time_deltas,
            "rows": rows_length
        }
        
        total_time = time_deltas['net_total']
        print(f"\n{name.upper():<8} | Total: {total_time:.6f} sec | Rows: {rows_length:,}")
        print("   " + "-" * 52)

        start_uss = uss_history[0]
        end_uss = uss_history[-1]
        highest_uss = max(uss_history)
        
        net_mem_mb = (end_uss - start_uss) / (1024 * 1024)
        peak_mem_mb = (highest_uss - start_uss) / (1024 * 1024)

        print(f"    Start USS   : {start_uss / (1024 * 1024):>8.5f} MiB ({start_uss:,} bytes)")
        print(f"    End USS     : {end_uss / (1024 * 1024):>8.5f} MiB ({end_uss:,} bytes)")
        print(f"    Highest USS : {highest_uss / (1024 * 1024):>8.5f} MiB ({highest_uss:,} bytes)")
        print(f"    Net Delta   : {net_mem_mb:>+8.5f} MiB")
        print(f"    Peak Delta  : {peak_mem_mb:>8.5f} MiB")
        print("   " + "-" * 52)
        
        steps = ['getMetric', 'get_top_ctr', 'get_top_cpa', 'save_top_ctr', 'save_top_cpa']
        for step in steps:
            t_val = time_deltas[step]
            print(f"    {step:<14} : {t_val:.6f} sec")
        print("   " + "=" * 52)

if __name__ == "__main__":
    main()