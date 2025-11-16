# test_client.py
import requests
import json

# The URL for your running FastAPI application's submission endpoint
API_URL = "http://127.0.0.1:8000/submit"

complaint_data = {
    "pnr": "1234567890",
    "complaint_type": "Punctuality",
    "complaint": "My train was delayed by over 5 hours yesterday without any information."
}

# --- Script Execution ---
print(f"▶️  Attempting to send POST request to: {API_URL}")
print("   -------------------------------------------------")
# Pretty-print the data being sent for clarity
print(f"   Payload being sent:\n{json.dumps(complaint_data, indent=2)}")
print("   -------------------------------------------------")

try:
    # Send the POST request with the JSON data
    response = requests.post(API_URL, json=complaint_data)
    
    # This line will raise an exception for error status codes (4xx or 5xx)
    response.raise_for_status() 

    # If the request was successful, print the response
    print("\n✅ Success! Response Received from Server:")
    print("   -------------------------------------------------")
    print(f"   Status Code: {response.status_code}")
    
    # Pretty-print the JSON response from the server
    print("   Response JSON:")
    print(json.dumps(response.json(), indent=2))
    print("   -------------------------------------------------")

# --- Error Handling ---
except requests.exceptions.ConnectionError:
    print("\n❌ CRITICAL ERROR: Connection Failed.")
    print(f"   Could not connect to the server at {API_URL}.")
    print("   Is the FastAPI server running? You can start it with:")
    print("   uvicorn app:app --reload")

except requests.exceptions.HTTPError as err:
    print(f"\n❌ HTTP Error occurred: {err}")
    print(f"   Status Code: {err.response.status_code}")
    # Try to print the error detail from the server's JSON response
    try:
        print(f"   Server says: {err.response.json()}")
    except json.JSONDecodeError:
        print(f"   Response was not in JSON format: {err.response.text}")

except Exception as err:
    print(f"\nAn unexpected error occurred: {err}")
