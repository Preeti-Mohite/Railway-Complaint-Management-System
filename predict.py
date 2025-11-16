import joblib

# Load model and vectorizer
clf = joblib.load("complaint_model.joblib")
vectorizer = joblib.load("tfidf_vectorizer.joblib")

# Example new complaints
new_complaints = [
    "No water in toilet and very dirty washroom",
    "Train delayed by 4 hours without any announcement",
    "Ticket cancelled but refund not received yet",
    "Passenger misbehaving in the coach, no RPF available"
]

# Transform and predict
new_tfidf = vectorizer.transform(new_complaints)
predictions = clf.predict(new_tfidf)

# Show results
for complaint, dept in zip(new_complaints, predictions):
    print(f"{complaint}  -->  {dept}")
