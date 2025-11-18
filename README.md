# lbal-backend

Initial FastAPI backend scaffold for the LBAL marketplace platform. This project includes a minimal
service layout, database models, and CI pipeline so new features can be added quickly.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Use `docker-compose up --build` for running the API with Postgres and Redis locally.
