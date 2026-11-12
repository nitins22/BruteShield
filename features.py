import sqlite3
from collections import defaultdict

DB_PATH = "logs/bruteshield.db"


def get_all_attempts():
    # sab attempts nikal lo, IP-wise order me taaki groups banane me aasani ho
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT ip, username, success, timestamp FROM login_attempts ORDER BY ip, timestamp"
    ).fetchall()
    conn.close()
    return rows


def extract_features():
    rows = get_all_attempts()

    # ek hi IP ke sab attempts ek jagah group kar do
    ip_data = defaultdict(list)
    for row in rows:
        ip_data[row["ip"]].append(row)

    all_features = []

    for ip, attempts in ip_data.items():
        total_attempts = len(attempts)
        failed_attempts = sum(1 for a in attempts if a["success"] == 0)
        distinct_usernames = len(set(a["username"] for a in attempts))

        # time gaps nikalne ke liye timestamps ko order me rakhna zaroori hai
        timestamps = sorted(a["timestamp"] for a in attempts)
        if len(timestamps) > 1:
            gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            avg_gap = round(sum(gaps) / len(gaps), 2)
            min_gap = round(min(gaps), 2)
        else:
            # sirf ek hi attempt hai to gap calculate nahi ho sakta
            avg_gap = None
            min_gap = None

        failure_ratio = round(failed_attempts / total_attempts, 2) if total_attempts else 0

        all_features.append({
            "ip": ip,
            "total_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "distinct_usernames": distinct_usernames,
            "avg_time_gap_seconds": avg_gap,
            "min_time_gap_seconds": min_gap,
            "failure_ratio": failure_ratio,
        })

    return all_features


def print_as_table(features):
    headers = ["IP", "Total", "Failed", "Distinct Users", "Avg Gap(s)", "Min Gap(s)", "Fail Ratio"]
    col_widths = [16, 7, 8, 15, 12, 12, 11]

    header_row = "".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * sum(col_widths))

    for f in features:
        row = [
            f["ip"],
            str(f["total_attempts"]),
            str(f["failed_attempts"]),
            str(f["distinct_usernames"]),
            str(f["avg_time_gap_seconds"]),
            str(f["min_time_gap_seconds"]),
            str(f["failure_ratio"]),
        ]
        print("".join(val.ljust(w) for val, w in zip(row, col_widths)))


if __name__ == "__main__":
    features = extract_features()
    print_as_table(features)
