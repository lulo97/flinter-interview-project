import os
import time
import polars as pl

def getMetric(filename):
    #Lazy mode
    lazy_df = pl.scan_csv(filename)

    total_raw_rows = lazy_df.select(pl.len()).collect().item()

    agg_query = (
        lazy_df.group_by("campaign_id")
        .agg([
            pl.col("impressions").sum(),
            pl.col("clicks").sum(),
            pl.col("spend").sum(),
            pl.col("conversions").sum(),
        ])
        .with_columns([
            (pl.col("clicks") / pl.col("impressions"))
                .fill_nan(0)
                .fill_null(0)
                .alias("ctr"),
            (pl.col("spend") / pl.col("conversions"))
                .fill_nan(0)
                .fill_null(0)
                .alias("cpa"),
        ])
    )

    #Streaming to process chunk by chunk with large data size
    agg_resolved = agg_query.collect(streaming=True)

    return agg_resolved, total_raw_rows + 1

#Using top_k O(n) instead of sort O(nlogn)
def getTop10HighestCTR(metrics: pl.DataFrame):
    return metrics.top_k(10, by="ctr")

def getTop10LowestCPA(metrics: pl.DataFrame):
    return metrics.bottom_k(10, by="cpa")

def save_to_csv(df: pl.DataFrame, filename: str) -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)
    df.write_csv(full_path)


if __name__ == "__main__":
    filename = "ad_data.csv"

    start_time = time.perf_counter()

    metrics, rows_length = getMetric(filename)

    top_10_highest_ctr = getTop10HighestCTR(metrics)
    top_10_lowest_cpa = getTop10LowestCPA(metrics)

    save_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    print(f"Optimized Execution time: {end_time - start_time:.6f} seconds")
