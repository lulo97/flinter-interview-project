import os
import time

def getMetric(filename):
    with open(filename, "r") as file:
        content = file.read().strip()

    rows = content.split("\n");

    header = rows[0].split(",")

    metrics = []

    agg = {}
    for line in rows[1:]:
        cells = line.split(",")
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

def save_to_csv(data, filename) -> None:
    headers = list(data[0].keys())

    header_line = ",".join(headers)
    csv_rows = [header_line]

    for row in data:
        row_line = ",".join(str(row.get(key, "")) for key in headers)
        csv_rows.append(row_line)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filename)

    with open(full_path, "w", encoding="utf-8") as file:
        file.write("\n".join(csv_rows) + "\n")

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

    #Execution time: 0.003560 seconds on 200 lines
    print(f"Execution time: {end_time - start_time:.6f} seconds on {rows_length} lines")