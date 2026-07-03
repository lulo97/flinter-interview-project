import os
import time
import polars as pl

def getMetric(filename):
    df = pl.read_csv(filename)

    agg = (
        df.group_by("campaign_id")
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

    return agg, df.height + 1


def getTop10HighestCTR(metrics: pl.DataFrame):
    return metrics.sort("ctr", descending=True).head(10)


def getTop10LowestCPA(metrics: pl.DataFrame):
    return metrics.sort("cpa", descending=False).head(10)


def save_df_to_csv(df: pl.DataFrame, filename: str) -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)
    df.write_csv(full_path)


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

    save_df_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_df_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    #Execution time: 0.013073 seconds on 200 lines
    print(f"Execution time: {end_time - start_time:.6f} seconds on {rows_length} lines")