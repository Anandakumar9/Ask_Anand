# Running the StudyPulse Backend (FastAPI)

## 1. Local Development (SQLite, No Docker)

1. Open a terminal and navigate to the backend directory:
   ```sh
   cd studypulse/backend
   ```
2. (Optional) Create and activate a virtual environment:
   ```sh
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Mac/Linux
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```sh
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. The API will be available at http://localhost:8000

## 2. With Docker Compose (PostgreSQL, Redis)

1. Uncomment the `backend` service in `studypulse/docker-compose.yml`.
2. From the `studypulse` directory, run:
   ```sh
   docker-compose up -d
   ```
3. The API will be available at http://localhost:8000

---

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
