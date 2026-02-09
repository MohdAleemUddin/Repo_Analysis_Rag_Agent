import pytest
import csv
from pathlib import Path

def test_csv_matrix_row_count():
    csv_path = Path(__file__).parent / "agent_core_functional_tests.csv"
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) >= 3

def test_csv_matrix_content():
    csv_path = Path(__file__).parent / "agent_core_functional_tests.csv"
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert "Test Case" in rows[0]
