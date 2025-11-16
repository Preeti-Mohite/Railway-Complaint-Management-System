import json
import os
from passlib.context import CryptContext
import getpass

# --- Configuration ---
USERS_FILE = "users.json"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_staff_member():
    """A secure command-line tool to add a new staff member."""
    print("--- Railway Staff Account Creation Tool ---")
    
    # 1. Get username
    username = input("Enter new staff username: ").strip()
    if not username:
        print("❌ Error: Username cannot be empty.")
        return

    # 2. Load existing users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = {}
    else:
        users = {}
        
    if username in users:
        print(f"❌ Error: Username '{username}' already exists.")
        return

    # 3. Get password (MODIFIED: Now uses input() to make it visible)
    password = input("Enter new password (min 6 chars): ")
    if len(password) < 6:
        print("❌ Error: Password must be at least 6 characters long.")
        return
        
    password_confirm = input("Confirm password: ")
    if password != password_confirm:
        print("❌ Error: Passwords do not match.")
        return

    # 4. Hash the password and create the simplified user object
    hashed_password = pwd_context.hash(password)
    users[username] = {
        "username": username,
        "password": hashed_password
    }

    # 5. Save the updated user list
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

    print(f"\n✅ Success! Staff member '{username}' has been added.")

if __name__ == "__main__":
    add_staff_member()

