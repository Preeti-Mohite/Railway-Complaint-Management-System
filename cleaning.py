# cleaning.py
import pandas as pd
import re
import os

# --- Configuration ---
INPUT_FILE = "D:\\mpcopy\\2000 dataset.xlsx"
OUTPUT_FILE = "Dataset_cleaned.csv"

# --- Cleaning Functions 
def clean_text(text):
    if pd.isna(text): return ""
    text = str(text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_pnr(text):
    if pd.isna(text): return None
    text = str(text)
    match = re.search(r"\b\d{10}\b", text)
    return match.group(0) if match else None

# --- Main Script Logic ---
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: The input file '{INPUT_FILE}' was not found.")
        print("   Please make sure your Excel file is in the same directory.")
        return

    print(f"🔄 Loading data from Excel file: '{INPUT_FILE}'...")
    
    # --- THIS IS THE KEY FIX ---
    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        print("   Please ensure 'openpyxl' is installed (`pip install openpyxl`).")
        return

    if 'Complaint' not in df.columns or 'Department' not in df.columns:
        print(f"❌ Error: 'Complaint' or 'Department' column not found in {INPUT_FILE}.")
        return

    print("🧼 Cleaning data...")
    df_cleaned = pd.DataFrame()
    # Ensure all columns are present before assigning
    if "Serial_Number" in df.columns:
        df_cleaned["Serial_Number"] = df["Serial_Number"]
    
    df_cleaned["PNR"] = df["Complaint"].apply(extract_pnr)
    df_cleaned["Complaint"] = df["Complaint"].apply(clean_text)
    df_cleaned['Department'] = df['Department']
    
    # Save the cleaned data to a new CSV 
    df_cleaned.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"✅ Success! Cleaned data has been saved to '{OUTPUT_FILE}'.")
    print(f"   Processed {len(df_cleaned)} rows of data.")

if __name__ == "__main__":
    main()

