# Setup instructions

Install Python 3.11.9, uv 0.11.16.

Open project .\flinter-interview-project and run commands:
    uv venv
    uv pip install -r requirements.txt

# How to run the program

Run run.bat file (Windows only) to run both venv enviroment and excute python file.
Or run with command "python src\implement\app.py"

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
- src\implement\result\top10_cpa.csv
    campaign_id,total_impressions,total_clicks,total_spend,total_conversions,CTR,CPA
    CMP016,13686317849,375883156,393677129.86,20410131,0.0275,19.29
    CMP049,13678441909,375790166,393822976.90,20408613,0.0275,19.30
    CMP032,13707961325,376277379,395003523.04,20469062,0.0274,19.30
    CMP034,13663387190,375490759,394029600.32,20403716,0.0275,19.31
    CMP040,13707493063,376364561,395064372.66,20444877,0.0275,19.32
    CMP004,13705584584,376906722,395992597.40,20491770,0.0275,19.32
    CMP047,13704337167,376533784,395185526.77,20447393,0.0275,19.33
    CMP045,13689842314,376256850,394756303.73,20424317,0.0275,19.33
    CMP022,13703365735,377109904,395899684.64,20480486,0.0275,19.33
    CMP024,13665607452,375614418,394482754.56,20406008,0.0275,19.33
- src\implement\result\top10_ctr.csv
    campaign_id,total_impressions,total_clicks,total_spend,total_conversions,CTR,CPA
    CMP005,13648608306,375627610,394780333.96,20403485,0.0275,19.35
    CMP022,13703365735,377109904,395899684.64,20480486,0.0275,19.33
    CMP023,13657508417,375769033,394203576.87,20390213,0.0275,19.33
    CMP011,13714973625,377330481,396309000.78,20463005,0.0275,19.37
    CMP018,13708338704,377076026,396003175.53,20477639,0.0275,19.34
    CMP026,13652760288,375491308,394442607.58,20370126,0.0275,19.36
    CMP019,13675562649,376096719,395062881.56,20415450,0.0275,19.35
    CMP042,13717935895,377260350,396576467.39,20507021,0.0275,19.34
    CMP004,13705584584,376906722,395992597.40,20491770,0.0275,19.32
    CMP027,13719269461,377233894,396153928.92,20462054,0.0275,19.36


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