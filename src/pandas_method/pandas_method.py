import os
import time
import pandas as pd

def getMetric(filename):
    #1gb file csv is still small for mordern ram so skip chunksize in read_csv()
    df = pd.read_csv(filename)

    agg = df.groupby("campaign_id", as_index=False).agg(
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        spend=("spend", "sum"),
        conversions=("conversions", "sum"),
    )

    agg["ctr"] = agg["clicks"] / agg["impressions"].replace(0, pd.NA)
    agg["ctr"] = agg["ctr"].fillna(0)

    agg["cpa"] = agg["spend"] / agg["conversions"].replace(0, pd.NA)
    agg["cpa"] = agg["cpa"].fillna(0)

    return agg, len(df) + 1


def getTop10HighestCTR(metrics):
    return metrics.sort_values("ctr", ascending=False).head(10)


def getTop10LowestCPA(metrics):
    return metrics.sort_values("cpa", ascending=True).head(10)


def save_to_csv(data, filename) -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)
    data.to_csv(full_path, index=False)


if __name__ == "__main__":

    # campaign_id,date,impressions,clicks,spend,conversions
    # CMP025,2025-04-18,3653,60,64.29,2
    # CMP020,2025-05-03,24465,764,1394.62,42
    # CMP019,2025-02-05,7214,236,135.93,21
    # CMP046,2025-06-04,10631,201,298.82,18
    # CMP044,2025-03-26,31942,964,744.4,37
    # CMP041,2025-02-22,37210,984,1716.18,32
    # CMP036,2025-01-04,7112,265,227.31,22
    # CMP043,2025-06-10,1074,34,56.89,1
    filename = "ad_data_small.csv"

    start_time = time.perf_counter()

    metrics, rows_length = getMetric(filename)

    top_10_highest_ctr = getTop10HighestCTR(metrics)
    top_10_lowest_cpa = getTop10LowestCPA(metrics)

    save_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    #Execution time: 0.023644 seconds on 200 lines
    print(f"Execution time: {end_time - start_time:.6f} seconds on {rows_length} lines")