import pandas as pd
import sys
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib

file_path = "Dataset_cleaned.csv" 
try:
    df = pd.read_csv(file_path)
    print(f"✅ Dataset '{file_path}' loaded successfully. Shape: {df.shape}")
    print(f"   Columns found: {df.columns.tolist()}")
except FileNotFoundError:
    print(f"❌ ERROR: The file '{file_path}' was not found. Please make sure it's in the same directory.")
    sys.exit(1)

# Ensure the required columns ("Complaint", "Department") are present
required_cols = ["Complaint", "Department"]
for col in required_cols:
    if col not in df.columns:
        print(f"❌ ERROR: Required column '{col}' not found in the dataset. Please check the CSV headers.")
        sys.exit(1)

# DATA CLEANING AND PREPROCESSING
print("\n🔄 Starting data cleaning...")

# Drop any rows where 'Complaint' or 'Department' might be missing
df = df.dropna(subset=["Complaint", "Department"])

# Convert to string type and remove any leading/trailing whitespace
df["Complaint"] = df["Complaint"].astype(str).str.strip()
df["Department"] = df["Department"].astype(str).str.strip()

# Drop any rows that became empty after stripping
df = df[(df["Complaint"] != "") & (df["Department"] != "")]

# We still standardize the case to prevent treating "General" and "general" as different categories.
df["Department"] = df["Department"].str.title()

# Remove department classes with only one sample, as they cannot be stratified
df = df.groupby('Department').filter(lambda x: len(x) > 1)

print("✅ Cleaning complete.")
print(f"   - Final Shape after cleaning: {df.shape}")
print(f"   - Unique Departments Found: {df['Department'].unique().tolist()}")

# Final safety check: ensure there are at least two departments to classify between
if df["Department"].nunique() < 2:
    print("❌ ERROR: Dataset must have at least 2 unique departments for training.")
    sys.exit(1)


# 3. MODEL TRAINING
print("\n🚀 Starting model training...")

# Split data into features (X) and target (y)
X = df["Complaint"]
y = df["Department"]

# Step 3.2: Create training and testing sets. `stratify=y` ensures department
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Convert the text of the complaints into numerical TF-IDF vectors
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)
print("   - Text data has been vectorized.")

# Train the Logistic Regression classifier
clf = LogisticRegression(max_iter=1000, random_state=42)
clf.fit(X_train_tfidf, y_train)
print("   - Model training complete.")

# 4. EVALUATION AND SAVING

#  Evaluate the model's performance on the unseen test data
y_pred = clf.predict(X_test_tfidf)
print("\n📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

# Save the trained model and the vectorizer to disk
joblib.dump(clf, "complaint_model.joblib")
joblib.dump(vectorizer, "tfidf_vectorizer.joblib")
print("✅ Model ('complaint_model.joblib') and vectorizer ('tfidf_vectorizer.joblib') saved successfully!")
print("\n✨ Process finished!")
