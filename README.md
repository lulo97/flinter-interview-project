# Setup instructions

Install Python 3.11.9, uv 0.11.16.

Open project .\flinter-interview-project and run commands:
    uv venv
    uv pip install -r requirements.txt

# How to run the program

Run run.bat file (Windows only) to run both venv enviroment and excute python file

# Libraries used

numpy==2.5.0
pandas==3.0.3
polars==1.42.1
polars-runtime-32==1.42.1
psutil==7.2.2
pyarrow==24.0.0
python-dateutil==2.9.0.post0
six==1.17.0
tzdata==2026.2

# Documented decisions

Using python to solve challenge because this problem is a data processing problem which Python has many libaries support and easy to work with.

Using polars as primary library to process csv data because it's backended by Rust which is very fast (proved in src\benchmark\log.txt file).

Using polars's LazyFrame to utilize underlaying query optimizer of polars.

Using streaming mode to proces chunk by chunk to avoid out of memory error (agg_query.collect(streaming=True)).

Using top_k() with speed of O(NlogK) with k = 10 instead of sort() with speed of O(NlogN)

# Benchmark

Code for benmark located in src\benchmark\benchmark.py with output log in src\benchmark\log.txt

# Processing time for the 1GB file

Run file src\implement\app.py to get process time for 1GB file ranged from 1.5 second to 1.6 second.

Measured on Ryzen 7-7735HS, 16GB laptop.

Output file on: 
- src\implement\top10_cpa.csv
- src\implement\top10_ctr.csv

# Peak memory usage (if measured)

Benchmarking with file: ad_data.csv
--------------------------------------------------
Main thread: 4072 | Monitor thread: 16352

IMPLEMENT | Total: 1.544275 sec | Rows: 26,843,545
   ----------------------------------------------------
    Start USS   : 69.44922 MiB (72,822,784 bytes)
    End USS     : 234.83203 MiB (246,239,232 bytes)
    Highest USS : 235.54688 MiB (246,988,800 bytes)
    Net Delta   : +165.38281 MiB
    Peak Delta  : 166.09766 MiB
   ----------------------------------------------------
    getMetric      : 1.540921 sec
    get_top_ctr    : 0.000730 sec
    get_top_cpa    : 0.000351 sec
    save_top_ctr   : 0.001389 sec
    save_top_cpa   : 0.000884 sec
   ====================================================