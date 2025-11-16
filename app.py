# app.py 
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import joblib
import uuid
import json, os, time
from typing import Optional
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("FATAL ERROR: JWT_SECRET environment variable not set! Please create a .env file.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 120
DATA_FILE = "complaints.json"
USERS_FILE = "users.json"
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

# Create data file if it's missing on first run
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# --- LOAD ML MODEL & VECTORIZER ---
try:
    clf = joblib.load("complaint_model.joblib")
    vectorizer = joblib.load("tfidf_vectorizer.joblib")
    print("✅ Model and vectorizer loaded successfully.")
except FileNotFoundError:
    print("\n" + "="*50)
    print("❌ FATAL ERROR: Model files ('complaint_model.joblib' or 'tfidf_vectorizer.joblib') not found.")
    print("   Please run your data pipeline (`cleaning.py` and `train_model.py`) first.")
    print("="*50 + "\n")
    exit()

# --- FASTAPI INITIALIZATION ---
app = FastAPI(title="Railway Complaint System")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Mount the static directory to serve CSS, JS, etc.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- UTILITY FUNCTIONS ---
def create_access_token(payload: dict):
    """Creates a new JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = payload.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str):
    """Verifies a JWT token, raising an exception if invalid."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.PyJWTError, jwt.ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )

# --- AUTH DEPENDENCY ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """A FastAPI dependency that verifies the token and returns the payload."""
    return verify_token(credentials.credentials)

# --- PYDANTIC MODELS (for request body validation) ---
class SubmitModel(BaseModel):
    pnr: str
    complaint: str
    complaint_type: Optional[str] = "Other"

class LoginModel(BaseModel):
    username: str
    password: str

# --- API ROUTES ---

# --- Passenger-facing Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the main complaint submission page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
def submit(data: SubmitModel):
    """Handles new complaint submissions, predicts department, and saves it."""
    try:
        # Predict the department using the loaded model and vectorizer
        transformed_complaint = vectorizer.transform([data.complaint])
        prediction = clf.predict(transformed_complaint)[0]
        complaint_id = str(uuid.uuid4())[:8] # Generate a short, unique ID
        
        complaints = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                try:
                    complaints = json.load(f)
                except json.JSONDecodeError:
                    # If the file is empty or corrupted, start with an empty dict
                    complaints = {} 

        # Create the new complaint record
        complaints[complaint_id] = {
            "pnr": data.pnr,
            "submitted_at": time.time(),
            "complaint": data.complaint,
            "predicted": [{"department": prediction, "score": 1.0}], # Standardize format
            "assigned_departments": [prediction], # Initially assign to predicted dept.
            "status": "Pending"
        }
        
        with open(DATA_FILE, "w") as f:
            json.dump(complaints, f, indent=4)
            
        return {"complaint_id": complaint_id, "predicted": [{"department": prediction}]}
    except Exception as e:
        print(f"Error during prediction or file operation: {e}")
        raise HTTPException(status_code=500, detail="Error processing the complaint.")

@app.get("/status/{complaint_id}")
def status_check(complaint_id: str):
    """Allows passengers to check the status of their complaint."""
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail={"error": "Complaint data not found."})
    with open(DATA_FILE, "r") as f:
        complaints = json.load(f)
    if complaint_id not in complaints:
        raise HTTPException(status_code=404, detail={"error": "Complaint ID not found"})
    return complaints[complaint_id]


# --- Staff-facing Routes (Protected) ---
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    """Serves the admin dashboard page. The dependency protects this route."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/admin/login")
def admin_login(data: LoginModel):
    """Authenticates a staff member and returns a JWT token."""
    if not os.path.exists(USERS_FILE):
        raise HTTPException(status_code=500, detail="User file not found. Please create a staff user first.")
        
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    
    user = users.get(data.username)
    # Securely verify the provided password against the stored hash
    if not user or not pwd_context.verify(data.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create a simple payload for the JWT token
    payload = {"username": user["username"]}
    token = create_access_token(payload)
    
    # Return the token AND the user object, as required by the frontend
    return {"access_token": token, "token_type": "bearer", "user": payload}

@app.get("/admin/complaints", dependencies=[Depends(get_current_user)])
def admin_get_complaints():
    """Returns all complaints. Protected route."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@app.post("/admin/update/{complaint_id}", dependencies=[Depends(get_current_user)])
def admin_update(complaint_id: str, status: str, departments: str):
    """Updates the status and assigned departments of a complaint. Protected route."""
    if not os.path.exists(DATA_FILE): 
        raise HTTPException(status_code=404, detail="Complaint data file not found")

    with open(DATA_FILE, "r") as f:
        complaints = json.load(f)
        
    if complaint_id not in complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Update the complaint details
    complaints[complaint_id]["status"] = status
    complaints[complaint_id]["assigned_departments"] = [d.strip() for d in departments.split(',')]

    with open(DATA_FILE, "w") as f:
        json.dump(complaints, f, indent=4)

    return {"message": "Updated successfully"}