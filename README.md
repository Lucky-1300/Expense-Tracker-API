# Expense Tracker API

A RESTful Expense Tracker API built with Python and FastAPI. The application uses CSV storage for persisting expense records and Pandas/NumPy for spending analytics.

## Tech Stack

- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Data Analytics**: Pandas, NumPy
- **Validation**: Pydantic
- **Storage**: CSV (`data/expenses.csv`)

## Project Structure

```text
expense_tracker_api/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── services.py
│   ├── analytics.py
│   ├── utils.py
│   └── config.py
├── data/
│   └── expenses.csv
├── tests/
│   └── test_api.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup Instructions

### 1. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API Server

```bash
uvicorn app.main:app --reload
```
