import os
import time

def getMetricByCampaignId(campaign_id, rows):
    total_impressions = 0
    total_clicks = 0
    total_spend = 0
    total_conversions = 0

    for row in rows:
        cells = row.split(",")
        if cells[0] == campaign_id:
            total_impressions += int(cells[2])
            total_clicks += int(cells[3])
            total_spend += float(cells[4])
            total_conversions += float(cells[5])

    CTR = total_clicks / total_impressions
    CPA = total_spend / total_conversions if total_conversions else 0

    return {
        "campaign_id": campaign_id,
        "impressions": total_impressions,
        "clicks": total_clicks,
        "spend": total_spend,
        "conversions": total_conversions,
        "ctr": CTR,
        "cpa": CPA
    }

def getMetric(filename):
    with open(filename, "r") as file:
        content = file.read().strip()

    rows = content.split("\n");

    header = rows[0].split(",")

    metrics = []

    for i in range(1, len(rows) - 1):
        campaign_id = rows[i].split(",")[0]
        exists = any(d.get("campaign_id") == campaign_id for d in metrics)
        if (exists):
            continue
        metrics.append(getMetricByCampaignId(campaign_id, rows))
    
    return metrics, rows;

def getTop10HighestCTR(metrics):
    return sorted(metrics, key=lambda x: x['ctr'], reverse=True)[0:10]

def getTop10LowestCPA(metrics):
    return sorted(metrics, key=lambda x: x['cpa'], reverse=False)[0:10]

def save_dicts_to_csv(data, filename) -> None:
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

    metrics, rows = getMetric(filename)

    top_10_highest_ctr = getTop10HighestCTR(metrics)
    top_10_lowest_cpa = getTop10LowestCPA(metrics)

    save_dicts_to_csv(top_10_highest_ctr, "top10_ctr.csv")
    save_dicts_to_csv(top_10_lowest_cpa, "top10_cpa.csv")

    end_time = time.perf_counter()

    print(f"Execution time: {end_time - start_time:.6f} seconds on {len(rows)} lines")