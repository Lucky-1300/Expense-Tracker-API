"""Pydantic models and schemas for data validation."""

import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SortField(str, Enum):
    id = "id"
    title = "title"
    amount = "amount"
    category = "category"
    date = "date"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class ExpenseBase(BaseModel):
    """Base schema containing common expense fields."""

    title: str = Field(..., min_length=1, description="Expense title (non-empty)")
    amount: float = Field(..., gt=0, description="Expense amount (greater than 0)")
    category: str = Field(..., min_length=1, description="Expense category (non-empty)")
    date: datetime.date = Field(..., description="Date of expense in YYYY-MM-DD format")
    notes: Optional[str] = Field(default=None, description="Optional notes")

    @field_validator("title", "category")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must not be empty or whitespace only")
        return value.strip()

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value):
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date must be in valid YYYY-MM-DD format")
        return value


class ExpenseCreate(ExpenseBase):
    """Model used when creating an expense. Client does not control the id."""

    pass


class ExpenseUpdate(BaseModel):
    """Model used when updating an expense. All fields are optional."""

    title: Optional[str] = Field(default=None, min_length=1)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, min_length=1)
    date: Optional[datetime.date] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    @field_validator("title", "category")
    @classmethod
    def validate_non_empty_optional_string(
        cls, value: Optional[str]
    ) -> Optional[str]:
        if value is not None:
            if not value or not value.strip():
                raise ValueError("Field must not be empty or whitespace only")
            return value.strip()
        return value

    @field_validator("date", mode="before")
    @classmethod
    def validate_optional_date_format(cls, value):
        if value is not None and isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date must be in valid YYYY-MM-DD format")
        return value


class Expense(ExpenseBase):
    """Full Expense model including unique integer id."""

    id: int = Field(..., ge=1, description="Unique integer expense ID")


class ExpenseStatistics(BaseModel):
    """Overall statistics report schema."""

    total_expenses: float = Field(..., description="Sum of all expenses")
    expense_count: int = Field(..., description="Total count of expenses")
    average_expense: float = Field(..., description="Average expense amount")
    highest_expense: float = Field(..., description="Highest single expense amount")
