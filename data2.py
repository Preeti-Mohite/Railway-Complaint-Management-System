# data2.py (Corrected for Final.xlsx)
# This script is now aligned with the data loading and cleaning
# logic used in your main train_model.py script.

import pandas as pd
import os
from sklearn.model_selection import train_test_split

# --- MODIFIED: Pointing to your new dataset ---
INPUT_FILE = "Dataset_cleaned.csv"

def main():
    """Loads and processes the new dataset for analysis."""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: The file '{INPUT_FILE}' was not found.")
        return

    print(f"🔄 Loading data from '{INPUT_FILE}'...")
    df = pd.read_csv(INPUT_FILE)

    print("🛠️  Preparing data...")
    # Step 1: Drop rows with missing values
    df = df.dropna(subset=["Complaint", "Department"])

    # Step 2: Convert to string and strip spaces
    df["Complaint"] = df["Complaint"].astype(str).str.strip()
    df["Department"] = df["Department"].astype(str).str.strip()

    # Step 3: Drop any empty values that resulted from stripping
    df = df[(df["Complaint"] != "") & (df["Department"] != "")]

    # --- MODIFIED: Removed the old, unnecessary .replace() dictionary ---
    # Standardize capitalization to be consistent.
    df["Department"] = df["Department"].str.title()

    # Step 4: Drop rare classes to ensure proper splitting
    df = df.groupby("Department").filter(lambda x: len(x) > 1)

    print("\n--- Department Counts ---")
    print(df["Department"].value_counts())

    # Features and labels
    X = df["Complaint"]
    y = df["Department"]

    # Train-test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n✅ Data preparation complete.")
    print(f"   - Total samples: {len(df)}")
    print(f"   - Training samples: {len(X_train)}")
    print(f"   - Testing samples: {len(X_test)}")

if __name__ == "__main__":
    main()
