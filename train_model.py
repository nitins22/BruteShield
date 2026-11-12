import joblib
from features import extract_features
from sklearn.ensemble import IsolationForest


def prepare_data():
    features = extract_features()

    # ML model ko sirf numbers chahiye, IP address jaisa text nahi
    # isliye har IP ke liye ek "numbers wali row" banate hain
    X = []
    ip_list = []

    for f in features:
        row = [
            f["total_attempts"],
            f["failed_attempts"],
            f["distinct_usernames"],
            f["avg_time_gap_seconds"] if f["avg_time_gap_seconds"] is not None else 0,
            f["min_time_gap_seconds"] if f["min_time_gap_seconds"] is not None else 0,
            f["failure_ratio"],
        ]
        X.append(row)
        ip_list.append(f["ip"])

    return X, ip_list


if __name__ == "__main__":
    X, ip_list = prepare_data()
    print("Columns: [total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]\n")
    for ip, row in zip(ip_list, X):
        print(ip, "->", row)

    model = IsolationForest(random_state=42)
    print("\nModel created:", model)

    model.fit(X)
    print("Model trained on", len(X), "IP records.")

    predictions = model.predict(X)

    print("\nResults:")
    for ip, pred in zip(ip_list, predictions):
        label = "SUSPICIOUS" if pred == -1 else "Normal"
        print(f"{ip}  ->  {label}")

    joblib.dump(model, "trained_model.pkl")
    print("\nModel saved to trained_model.pkl")
