"""Utility functions and common helpers for CSV persistence and storage."""

import csv
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from app.config import CSV_HEADERS, EXPENSES_CSV_PATH


class CSVStorageError(Exception):
    """Base exception for CSV storage operations."""

    pass


class MalformedCSVError(CSVStorageError):
    """Raised when a CSV file is corrupted, malformed, or missing required columns."""

    pass


def ensure_csv_file_exists(file_path: Path = EXPENSES_CSV_PATH) -> None:
    """
    Ensure the CSV file exists and has the required header.
    Preserves existing content; only initializes headers if the file does not exist
    or is completely empty (0 bytes).
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists() or file_path.stat().st_size == 0:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
    except OSError as exc:
        raise CSVStorageError(
            f"Failed to initialize CSV storage at {file_path}: {exc}"
        ) from exc


def read_expenses_csv(file_path: Path = EXPENSES_CSV_PATH) -> List[Dict[str, str]]:
    """
    Read all rows from the CSV file as a list of dictionaries.
    Validates CSV header and row structure.
    Raises MalformedCSVError if the file structure is invalid or corrupt.
    """
    ensure_csv_file_exists(file_path)

    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Check if header is present
            if reader.fieldnames is None:
                return []

            missing_headers = [h for h in CSV_HEADERS if h not in reader.fieldnames]
            if missing_headers:
                raise MalformedCSVError(
                    f"CSV at '{file_path}' is missing required headers: {missing_headers}"
                )

            rows: List[Dict[str, str]] = []
            for line_num, row in enumerate(reader, start=2):
                # Check for extra columns (captured under None key by DictReader)
                if None in row:
                    raise MalformedCSVError(
                        f"Malformed CSV at line {line_num} in '{file_path}': excess values found."
                    )

                # Check for missing column values
                if any(row.get(h) is None for h in CSV_HEADERS):
                    raise MalformedCSVError(
                        f"Malformed CSV at line {line_num} in '{file_path}': missing column values."
                    )

                rows.append(row)

            return rows

    except (csv.Error, UnicodeDecodeError) as exc:
        raise MalformedCSVError(
            f"Failed to read CSV at '{file_path}' due to malformed data: {exc}"
        ) from exc
    except OSError as exc:
        raise CSVStorageError(f"OS error reading CSV at '{file_path}': {exc}") from exc


def write_expenses_csv(
    rows: List[Dict[str, Any]], file_path: Path = EXPENSES_CSV_PATH
) -> None:
    """
    Atomically write the list of rows to the CSV file.
    Uses a temporary file in the same directory and replaces the target file,
    ensuring that partial writes never corrupt or erase user data.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = None
    temp_path = None

    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=file_path.parent,
            delete=False,
        )
        temp_path = Path(temp_file.name)

        writer = csv.DictWriter(
            temp_file, fieldnames=CSV_HEADERS, extrasaction="ignore"
        )
        writer.writerow({h: h for h in CSV_HEADERS})

        for row in rows:
            writer.writerow(row)

        temp_file.flush()
        temp_file.close()

        # Atomic replace
        os.replace(temp_path, file_path)

    except Exception as exc:
        if temp_file and not temp_file.closed:
            temp_file.close()
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise CSVStorageError(
            f"Failed to safely write CSV records to '{file_path}': {exc}"
        ) from exc


def append_expense_csv(
    row: Dict[str, Any], file_path: Path = EXPENSES_CSV_PATH
) -> None:
    """
    Append a single expense row to the CSV file safely.
    """
    ensure_csv_file_exists(file_path)

    try:
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=CSV_HEADERS, extrasaction="ignore"
            )
            writer.writerow(row)
    except OSError as exc:
        raise CSVStorageError(
            f"Failed to append record to CSV at '{file_path}': {exc}"
        ) from exc
