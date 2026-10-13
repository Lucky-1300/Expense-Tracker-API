"""Main entry point for the Expense Tracker FastAPI application."""

from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models import Expense, ExpenseCreate, ExpenseUpdate
from app.services import (
    create_expense as service_create_expense,
    delete_expense as service_delete_expense,
    get_all_expenses as service_get_all_expenses,
    get_expense_by_id as service_get_expense_by_id,
    update_expense as service_update_expense,
)
from app.utils import CSVStorageError, MalformedCSVError

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
def get_all_expenses():
    """Retrieve all expenses stored in data/expenses.csv."""
    return service_get_all_expenses()


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
