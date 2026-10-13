"""Isolated API and persistence tests for the Expense Tracker application."""

import csv
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

import app.main as api
from app import analytics, services
from app.models import ExpenseCreate, ExpenseUpdate, SortField, SortOrder
from app.utils import write_expenses_csv


class ExpenseAPITestCase(unittest.TestCase):
    """Exercise route handlers with a fresh temporary CSV for every test."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "expenses.csv"
        write_expenses_csv(
            [
                {
                    "id": "1",
                    "title": "Groceries",
                    "amount": "50.00",
                    "category": "Food",
                    "date": "2026-09-25",
                    "notes": "Weekly shop",
                },
                {
                    "id": "2",
                    "title": "Train ticket",
                    "amount": "30.00",
                    "category": "Travel",
                    "date": "2026-09-25",
                    "notes": "",
                },
                {
                    "id": "3",
                    "title": "Dinner",
                    "amount": "20.00",
                    "category": "Food",
                    "date": "2025-09-09",
                    "notes": "",
                },
            ],
            self.csv_path,
        )
        self.patches = patch.multiple(
            api,
            service_create_expense=lambda expense: services.create_expense(
                expense, self.csv_path
            ),
            service_get_expense_by_id=lambda expense_id: services.get_expense_by_id(
                expense_id, self.csv_path
            ),
            service_get_expenses=lambda **kwargs: services.get_expenses(
                file_path=self.csv_path, **kwargs
            ),
            service_update_expense=lambda expense_id, update: services.update_expense(
                expense_id, update, self.csv_path
            ),
            service_delete_expense=lambda expense_id: services.delete_expense(
                expense_id, self.csv_path
            ),
            get_monthly_spending_summary=lambda: analytics.get_monthly_spending_summary(
                self.csv_path
            ),
            get_category_spending_summary=lambda: analytics.get_category_spending_summary(
                self.csv_path
            ),
            get_statistics_report=lambda: analytics.get_statistics_report(
                self.csv_path
            ),
        )
        self.patches.start()

    def tearDown(self):
        self.patches.stop()
        self.temp_dir.cleanup()

    def list_expenses(self, **kwargs):
        defaults = {
            "category": None,
            "expense_date": None,
            "limit": None,
            "offset": 0,
            "sort_by": SortField.id,
            "order": SortOrder.asc,
        }
        defaults.update(kwargs)
        return api.get_all_expenses(**defaults)

    def test_add_expense_and_persistence_between_requests(self):
        created = api.create_expense(
            ExpenseCreate(
                title="Coffee",
                amount=4.5,
                category="Food",
                date="2026-10-01",
            )
        )

        self.assertEqual(created["id"], 4)
        expenses = self.list_expenses()
        self.assertEqual(len(expenses), 4)
        self.assertEqual(expenses[-1].title, "Coffee")

    def test_retrieve_all_expenses(self):
        expenses = self.list_expenses()

        self.assertEqual([expense.id for expense in expenses], [1, 2, 3])

    def test_retrieve_expense_by_id(self):
        expense = api.get_expense_by_id(2)

        self.assertEqual(expense.title, "Train ticket")

    def test_update_expense(self):
        updated = api.update_expense(
            1,
            ExpenseUpdate(amount=55, notes="Updated shop"),
        )

        self.assertEqual(updated.amount, 55)
        self.assertEqual(api.get_expense_by_id(1).notes, "Updated shop")

    def test_delete_expense(self):
        result = api.delete_expense(2)

        self.assertEqual(result["id"], 2)
        self.assertEqual([expense.id for expense in self.list_expenses()], [1, 3])

    def test_monthly_report_keeps_years_separate(self):
        self.assertEqual(
            api.monthly_report(),
            {"2025-09": 20.0, "2026-09": 80.0},
        )

    def test_category_report(self):
        self.assertEqual(
            api.category_report(),
            {"Food": 70.0, "Travel": 30.0},
        )

    def test_overall_statistics(self):
        self.assertEqual(
            api.statistics_report(),
            {
                "total_expenses": 100.0,
                "expense_count": 3,
                "average_expense": 33.33,
                "highest_expense": 50.0,
            },
        )

    def test_category_and_date_filtering(self):
        expenses = self.list_expenses(
            category="Food",
            expense_date=date(2026, 9, 25),
        )

        self.assertEqual([expense.id for expense in expenses], [1])

    def test_pagination_and_sorting(self):
        expenses = self.list_expenses(
            limit=2,
            offset=0,
            sort_by=SortField.amount,
            order=SortOrder.desc,
        )

        self.assertEqual([expense.id for expense in expenses], [1, 2])

    def test_csv_export(self):
        response = api.export_expenses(
            category=None,
            expense_date=None,
            limit=None,
            offset=0,
            sort_by=SortField.id,
            order=SortOrder.asc,
        )

        rows = list(csv.DictReader(response.body.decode("utf-8").splitlines()))
        self.assertEqual(response.media_type, "text/csv")
        self.assertEqual(response.headers["content-disposition"], "attachment; filename=expenses.csv")
        self.assertEqual([row["id"] for row in rows], ["1", "2", "3"])

    def test_invalid_amount_and_missing_fields(self):
        with self.assertRaises(ValidationError):
            ExpenseCreate(
                title="Invalid",
                amount=0,
                category="Food",
                date="2026-09-25",
            )

        with self.assertRaises(ValidationError):
            ExpenseCreate(amount=10, category="Food", date="2026-09-25")

    def test_nonexistent_expense_returns_not_found(self):
        with self.assertRaises(HTTPException) as context:
            api.get_expense_by_id(999)

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
