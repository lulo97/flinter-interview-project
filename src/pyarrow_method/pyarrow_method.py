import os
import time

import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.compute as pc

def getMetric(filename):
    table = csv.read_csv(
        filename,
        convert_options=csv.ConvertOptions(
            column_types={
                "campaign_id": pa.string(),
                "impressions": pa.int64(),
                "clicks": pa.int64(),
                "spend": pa.float64(),
                "conversions": pa.float64(),
            },
            include_columns=[
                "campaign_id",
                "impressions",
                "clicks",
                "spend",
                "conversions",
            ],
        ),
    )

    metrics = (
        table.group_by("campaign_id")
        .aggregate([
            ("impressions", "sum"),
            ("clicks", "sum"),
            ("spend", "sum"),
            ("conversions", "sum"),
        ])
    )

    ctr = pc.if_else(
        pc.equal(metrics["conversions_sum"], 0),  # placeholder, replaced below
        pa.scalar(0.0),
        pc.divide(metrics["clicks_sum"], metrics["impressions_sum"]),
    )

    # Better CTR calculation (avoid divide by zero)
    ctr = pc.if_else(
        pc.equal(metrics["impressions_sum"], 0),
        pa.scalar(0.0),
        pc.divide(metrics["clicks_sum"], metrics["impressions_sum"]),
    )

    cpa = pc.if_else(
        pc.equal(metrics["conversions_sum"], 0),
        pa.scalar(0.0),
        pc.divide(metrics["spend_sum"], metrics["conversions_sum"]),
    )

    metrics = metrics.append_column("ctr", ctr)
    metrics = metrics.append_column("cpa", cpa)

    return metrics, table.num_rows + 1


def getTop10HighestCTR(metrics):
    return metrics.sort_by([("ctr", "descending")]).slice(0, 10)


def getTop10LowestCPA(metrics):
    return metrics.sort_by([("cpa", "ascending")]).slice(0, 10)


def save_df_to_csv(data, filename):
    csv.write_csv(data, filename)

if __name__ == "__main__":
    filename = "ad_data_small.csv"

    start_time = time.perf_counter()

    metrics, rows_length = getMetric(filename)

    top_10_highest_ctr = getTop10HighestCTR(metrics)
    top_10_lowest_cpa = getTop10LowestCPA(metrics)

    save_df_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_df_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    #Execution time: 0.686505 seconds on 200 lines
    print(f"Execution time: {end_time - start_time:.6f} seconds on {rows_length} lines")