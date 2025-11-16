## How to Run the Project
1. **Clone the repository**
   ```bash
   git clone https://github.com/Preeti-Mohite/Railway-Complaint-Management-System.git

2. Go to the project folder
cd Railway-Complaint-Management-System

3.Install dependencies
pip install -r requirements.txt

4. Run the preprocessing and training scripts
 python cleaning.py
>> python predict.py
>> python train_model.py

5. Adding Staff member
python add_staff.py

6. Run the FastAPI application
uvicorn app:app --reload

7. Open the web app
http://127.0.0.1:8000

