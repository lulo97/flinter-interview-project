import os
import time
import csv

def getMetric(filename):
    with open(filename, "r", newline="") as file:
        #Avoid DictReader for faster reading
        reader = csv.reader(file)
        rows = list(reader)

    header = rows[0]
    data_rows = rows[1:]

    agg = {}
    for cells in data_rows:
        if not cells:
            continue
        cid = cells[0]
        m = agg.setdefault(cid, {
            "campaign_id": cid, "impressions": 0, "clicks": 0,
            "spend": 0.0, "conversions": 0.0
        })
        m["impressions"] += int(cells[2])
        m["clicks"] += int(cells[3])
        m["spend"] += float(cells[4])
        m["conversions"] += float(cells[5])

    metrics = []
    for m in agg.values():
        m["ctr"] = m["clicks"] / m["impressions"] if m["impressions"] else 0
        m["cpa"] = m["spend"] / m["conversions"] if m["conversions"] else 0
        metrics.append(m)

    return metrics, len(rows)

def getTop10HighestCTR(metrics):
    return sorted(metrics, key=lambda x: x['ctr'], reverse=True)[0:10]

def getTop10LowestCPA(metrics):
    return sorted(metrics, key=lambda x: x['cpa'], reverse=False)[0:10]

def save_dicts_to_csv(data, filename) -> None:
    headers = list(data[0].keys())

    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)

    with open(full_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":

    filename = "ad_data_small.csv"

    start_time = time.perf_counter()

    metrics, rows_length = getMetric(filename)

    top_10_highest_ctr = getTop10HighestCTR(metrics)
    top_10_lowest_cpa = getTop10LowestCPA(metrics)

    save_dicts_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_dicts_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    #Execution time: 0.003059 seconds on 200 lines
    print(f"Execution time: {end_time - start_time:.6f} seconds on {rows_length} lines")