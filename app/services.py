"""Services for handling expense data persistence and CRUD operations."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import EXPENSES_CSV_PATH
from app.models import Expense, ExpenseCreate, ExpenseUpdate
from app.utils import (
    MalformedCSVError,
    append_expense_csv,
    read_expenses_csv,
    write_expenses_csv,
)


def expense_to_dict(expense: Expense) -> Dict[str, Any]:
    """Convert an Expense model to a dictionary suitable for CSV serialization."""
    if expense.amount == round(expense.amount, 2):
        formatted_amount = f"{expense.amount:.2f}"
    else:
        formatted_amount = str(expense.amount)

    return {
        "id": str(expense.id),
        "title": expense.title,
        "amount": formatted_amount,
        "category": expense.category,
        "date": expense.date.isoformat(),
        "notes": expense.notes if expense.notes is not None else "",
    }


def row_to_expense(row: Dict[str, str]) -> Expense:
    """
    Parse and validate a raw CSV dictionary row into an Expense instance.
    Raises MalformedCSVError if the row contains invalid data types or malformed content.
    """
    try:
        raw_id = row.get("id", "").strip()
        if not raw_id.isdigit():
            raise ValueError(f"Invalid integer ID: '{raw_id}'")

        expense_id = int(raw_id)
        raw_notes = row.get("notes")
        notes = raw_notes.strip() if raw_notes and raw_notes.strip() else None

        return Expense(
            id=expense_id,
            title=row.get("title", ""),
            amount=float(row.get("amount", 0)),
            category=row.get("category", ""),
            date=row.get("date", ""),
            notes=notes,
        )
    except Exception as exc:
        raise MalformedCSVError(
            f"Failed to parse CSV row {row}: {exc}"
        ) from exc


def get_all_expenses(file_path: Path = EXPENSES_CSV_PATH) -> List[Expense]:
    """
    Retrieve all expenses stored in the CSV file.
    Does not silently drop corrupted rows; raises MalformedCSVError on malformed data.
    """
    raw_rows = read_expenses_csv(file_path)
    return [row_to_expense(row) for row in raw_rows]


def get_expense_by_id(
    expense_id: int, file_path: Path = EXPENSES_CSV_PATH
) -> Optional[Expense]:
    """
    Retrieve a specific expense by its integer ID.
    Returns None if no matching expense is found.
    """
    expenses = get_all_expenses(file_path)
    for expense in expenses:
        if expense.id == expense_id:
            return expense
    return None


def create_expense(
    expense_in: ExpenseCreate, file_path: Path = EXPENSES_CSV_PATH
) -> Expense:
    """
    Persist a new expense.
    Generates a unique integer ID (auto-incrementing from highest existing ID).
    The client does not control the ID.
    """
    existing_expenses = get_all_expenses(file_path)
    next_id = max((e.id for e in existing_expenses), default=0) + 1

    new_expense = Expense(id=next_id, **expense_in.model_dump())
    append_expense_csv(expense_to_dict(new_expense), file_path)
    return new_expense


def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    file_path: Path = EXPENSES_CSV_PATH,
) -> Optional[Expense]:
    """
    Update an existing expense by ID.
    Performs an atomic write to prevent data loss.
    Returns the updated Expense, or None if the expense does not exist.
    """
    existing_expenses = get_all_expenses(file_path)
    target_index = None

    for idx, expense in enumerate(existing_expenses):
        if expense.id == expense_id:
            target_index = idx
            break

    if target_index is None:
        return None

    update_data = expense_update.model_dump(exclude_unset=True)
    current_expense = existing_expenses[target_index]
    current_data = current_expense.model_dump()

    # Update only provided fields
    current_data.update(update_data)
    updated_expense = Expense(**current_data)
    existing_expenses[target_index] = updated_expense

    # Atomic write to ensure no data is lost
    write_expenses_csv(
        [expense_to_dict(e) for e in existing_expenses], file_path
    )
    return updated_expense


def delete_expense(
    expense_id: int, file_path: Path = EXPENSES_CSV_PATH
) -> bool:
    """
    Delete an expense by ID.
    Performs an atomic write of remaining records.
    Returns True if an expense was deleted, False if not found.
    """
    existing_expenses = get_all_expenses(file_path)
    initial_count = len(existing_expenses)

    remaining_expenses = [e for e in existing_expenses if e.id != expense_id]
    if len(remaining_expenses) == initial_count:
        return False

    write_expenses_csv(
        [expense_to_dict(e) for e in remaining_expenses], file_path
    )
    return True
