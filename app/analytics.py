"""Analytics and summary calculations using Pandas and NumPy."""

from pathlib import Path
from typing import Any, Dict
import numpy as np
import pandas as pd

from app.config import EXPENSES_CSV_PATH
from app.utils import ensure_csv_file_exists


def load_expenses_dataframe(file_path: Path = EXPENSES_CSV_PATH) -> pd.DataFrame:
    """
    Load expense records from CSV into a pandas DataFrame.
    Returns an empty DataFrame with the expected columns if the file has no data rows.
    """
    ensure_csv_file_exists(file_path)
    try:
        df = pd.read_csv(file_path, dtype={"id": "Int64", "notes": "string"})
    except (pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame(
            columns=["id", "title", "amount", "category", "date", "notes"]
        )

    if df.empty:
        return pd.DataFrame(
            columns=["id", "title", "amount", "category", "date", "notes"]
        )

    # Ensure amount and date are properly typed
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    # Drop rows that failed conversion
    df = df.dropna(subset=["amount", "date"])
    return df


def calculate_total_expenses(df: pd.DataFrame) -> float:
    """Calculate total spending as sum of amounts."""
    if df.empty:
        return 0.0
    return float(np.round(np.sum(df["amount"].to_numpy()), 2))


def calculate_expense_count(df: pd.DataFrame) -> int:
    """Calculate total number of expense records."""
    return int(len(df))


def calculate_average_expense(df: pd.DataFrame) -> float:
    """
    Calculate average expense amount: total spending divided by expense count.
    Handles empty data safely without division-by-zero errors.
    """
    if df.empty or len(df) == 0:
        return 0.0
    total = np.sum(df["amount"].to_numpy())
    avg = total / len(df)
    return float(np.round(avg, 2))


def calculate_highest_expense(df: pd.DataFrame) -> float:
    """Calculate highest single expense amount."""
    if df.empty:
        return 0.0
    return float(np.round(np.max(df["amount"].to_numpy()), 2))


def get_statistics_report(
    file_path: Path = EXPENSES_CSV_PATH,
) -> Dict[str, Any]:
    """
    Calculate overall statistical metrics from CSV:
    total expenses, expense count, average expense, and highest expense.
    """
    df = load_expenses_dataframe(file_path)
    return {
        "total_expenses": calculate_total_expenses(df),
        "expense_count": calculate_expense_count(df),
        "average_expense": calculate_average_expense(df),
        "highest_expense": calculate_highest_expense(df),
    }


def get_monthly_spending_summary(
    file_path: Path = EXPENSES_CSV_PATH,
) -> Dict[str, float]:
    """
    Calculate monthly spending summary grouped by calendar month and year (YYYY-MM).
    Ensures different years are not mixed.
    """
    df = load_expenses_dataframe(file_path)
    if df.empty:
        return {}

    df["month"] = df["date"].dt.strftime("%Y-%m")
    grouped = df.groupby("month")["amount"].sum().round(2)
    return {str(k): float(v) for k, v in grouped.to_dict().items()}


def get_category_spending_summary(
    file_path: Path = EXPENSES_CSV_PATH,
) -> Dict[str, float]:
    """
    Calculate category-wise spending summary grouped by category.
    """
    df = load_expenses_dataframe(file_path)
    if df.empty:
        return {}

    grouped = df.groupby("category")["amount"].sum().round(2)
    return {str(k): float(v) for k, v in grouped.to_dict().items()}
