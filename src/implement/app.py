import os
import time
import polars as pl

def getMetric(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The input file '{filename}' was not found.")
        
    if os.path.getsize(filename) == 0:
        raise ValueError(f"The input file '{filename}' is empty.")

    #Lazy mode
    lazy_df = pl.scan_csv(filename)

    try:
        total_raw_rows = lazy_df.select(pl.len()).collect().item()
    except pl.exceptions.NoDataError:
        raise Exception(f"File {filename} contains no valid data rows after filtering malformed rows.")
    except Exception as e:
        raise Exception(f"Failed to read raw row count: {e}")

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
                #Handle edge case by fill with 0
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

#Using top_k O(nlogk) instead of sort O(nlogn)
def getTop10HighestCTR(metrics: pl.DataFrame):
    return metrics.top_k(10, by="ctr")

def getTop10LowestCPA(metrics: pl.DataFrame):
    return metrics.bottom_k(10, by="cpa")

def save_to_csv(df: pl.DataFrame, filename: str) -> None:
    df = df.rename({
        "impressions": "total_impressions",
        "clicks": "total_clicks",
        "spend": "total_spend",
        "conversions": "total_conversions",
        "ctr": "CTR",
        "cpa": "CPA",
    })
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)

    df = df.with_columns([
        pl.col("total_spend").round(2).map_elements(lambda x: f"{x:.2f}", return_dtype=pl.String),
        pl.col("CTR").round(4).map_elements(lambda x: f"{x:.4f}", return_dtype=pl.String),
        pl.col("CPA").round(2).map_elements(lambda x: f"{x:.2f}", return_dtype=pl.String),
    ])

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

    print(f"Execution time: {end_time - start_time:.6f} seconds")
