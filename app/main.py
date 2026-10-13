"""Main entry point for the Expense Tracker FastAPI application."""

from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response

from app.analytics import (
    get_category_spending_summary,
    get_monthly_spending_summary,
    get_statistics_report,
)
from app.models import Expense, ExpenseCreate, ExpenseUpdate
from app.services import (
    create_expense as service_create_expense,
    delete_expense as service_delete_expense,
    get_expense_by_id as service_get_expense_by_id,
    get_expenses as service_get_expenses,
    update_expense as service_update_expense,
    expense_to_dict,
)
from app.models import SortField, SortOrder
from app.utils import CSVStorageError, MalformedCSVError, expenses_to_csv

app = FastAPI(
    title="Expense Tracker API",
    description="REST API for managing expenses and computing spending analytics.",
    version="1.0.0",
)


@app.exception_handler(MalformedCSVError)
def malformed_csv_handler(request: Request, exc: MalformedCSVError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"CSV storage corruption: {str(exc)}"},
    )


@app.exception_handler(CSVStorageError)
def csv_storage_handler(request: Request, exc: CSVStorageError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"CSV storage error: {str(exc)}"},
    )


@app.get("/", tags=["Health"])
def read_root():
    """Health check endpoint."""
    return {"message": "Expense Tracker API is running"}


@app.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED,
    tags=["Expenses"],
    summary="Create a new expense",
)
def create_expense(expense_in: ExpenseCreate):
    """
    Create a new expense record in data/expenses.csv.
    Client does not control ID; unique integer ID is auto-generated.
    Returns success message and created expense ID.
    """
    created_expense = service_create_expense(expense_in)
    return {
        "message": "Expense created successfully",
        "id": created_expense.id,
        "expense_id": created_expense.id,
        "expense": created_expense,
    }


@app.get(
    "/expenses",
    response_model=List[Expense],
    tags=["Expenses"],
    summary="Get all expenses",
)
def get_all_expenses(
    category: str | None = Query(default=None, min_length=1),
    expense_date: date | None = Query(default=None, alias="date"),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    sort_by: SortField = Query(default=SortField.id),
    order: SortOrder = Query(default=SortOrder.asc),
):
    """Retrieve all expenses stored in data/expenses.csv."""
    return service_get_expenses(
        category=category,
        expense_date=expense_date,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
    )


@app.get(
    "/expenses/export",
    tags=["Expenses"],
    summary="Export expenses as CSV",
)
def export_expenses(
    category: str | None = Query(default=None, min_length=1),
    expense_date: date | None = Query(default=None, alias="date"),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    sort_by: SortField = Query(default=SortField.id),
    order: SortOrder = Query(default=SortOrder.asc),
):
    """Download the selected expenses as a CSV file."""
    expenses = service_get_expenses(
        category=category,
        expense_date=expense_date,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
    )
    content = expenses_to_csv([expense_to_dict(expense) for expense in expenses])
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@app.get("/reports/monthly", tags=["Reports"], summary="Get monthly spending")
def monthly_report():
    """Return spending totals grouped by calendar month and year."""
    return get_monthly_spending_summary()


@app.get("/reports/category", tags=["Reports"], summary="Get category spending")
def category_report():
    """Return spending totals grouped by category."""
    return get_category_spending_summary()


@app.get("/reports/statistics", tags=["Reports"], summary="Get expense statistics")
def statistics_report():
    """Return total, count, average, and highest expense metrics."""
    return get_statistics_report()


@app.get(
    "/expenses/{expense_id}",
    response_model=Expense,
    tags=["Expenses"],
    summary="Get expense by ID",
)
def get_expense_by_id(expense_id: int):
    """Retrieve a specific expense by ID. Returns 404 if not found."""
    expense = service_get_expense_by_id(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )
    return expense


@app.put(
    "/expenses/{expense_id}",
    response_model=Expense,
    tags=["Expenses"],
    summary="Update an existing expense",
)
def update_expense(expense_id: int, expense_update: ExpenseUpdate):
    """
    Update an existing expense by ID.
    Returns 404 if the expense does not exist.
    Returns 422 if update fields are invalid.
    """
    updated_expense = service_update_expense(expense_id, expense_update)
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )
    return updated_expense


@app.delete(
    "/expenses/{expense_id}",
    tags=["Expenses"],
    summary="Delete an existing expense",
)
def delete_expense(expense_id: int):
    """
    Delete an expense by ID from data/expenses.csv.
    Returns 404 if the expense does not exist.
    """
    deleted = service_delete_expense(expense_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )
    return {
        "message": f"Expense with ID {expense_id} deleted successfully",
        "id": expense_id,
    }
