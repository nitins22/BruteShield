import joblib

# saved model wapas load kar rahe hain - training dobara nahi ho rahi
model = joblib.load("trained_model.pkl")
print("Model loaded from trained_model.pkl")

# ek naya, fake IP ka data - jaise abhi-abhi koi login attempt aaya ho
# format wahi hai jo train_model.py me use hua tha:
# [total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]
new_data = [[6, 6, 5, 0.15, 0.1, 1.0]]  # ek attacker jaisa pattern

prediction = model.predict(new_data)

if prediction[0] == -1:
    print("Result: SUSPICIOUS")
else:
    print("Result: Normal")
