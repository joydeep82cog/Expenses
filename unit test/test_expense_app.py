import pytest
from reference.models import Participant, Expense
from reference.utils import calculate_settlement, save_settlement_to_excel, load_trip_from_excel
import os
import tempfile
import pandas as pd

def test_participant_creation():
    p = Participant('Alice')
    assert p.name == 'Alice'

def test_expense_creation():
    e = Expense('Lunch', 100, 'Alice', ['Bob'], 'Shared meal')
    assert e.item == 'Lunch'
    assert e.amount == 100.0
    assert e.paid_by == 'Alice'
    assert e.omitted == ['Bob']
    assert e.notes == 'Shared meal'

def test_calculate_settlement_basic():
    participants = ['Alice', 'Bob']
    expenses = [Expense('Lunch', 100, 'Alice'), Expense('Dinner', 60, 'Bob')]
    balances = calculate_settlement(participants, expenses)
    assert pytest.approx(balances['Alice'], 0.01) == 20.0
    assert pytest.approx(balances['Bob'], 0.01) == -20.0

def test_calculate_settlement_with_omitted():
    participants = ['Alice', 'Bob', 'Charlie']
    expenses = [Expense('Lunch', 90, 'Alice', omitted=['Charlie'])]
    balances = calculate_settlement(participants, expenses)
    assert pytest.approx(balances['Alice'], 0.01) == 45.0
    assert pytest.approx(balances['Bob'], 0.01) == -45.0
    assert pytest.approx(balances['Charlie'], 0.01) == 0.0

def test_save_and_load_settlement_to_excel():
    participants = ['Alice', 'Bob']
    expenses = [Expense('Lunch', 100, 'Alice')]
    balances = calculate_settlement(participants, expenses)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = save_settlement_to_excel('TestTrip', participants, expenses, balances, tmpdir)
        assert os.path.exists(file_path)
        df_summary, df_expenses = load_trip_from_excel(file_path)
        assert 'Name' in df_summary.columns
        assert 'Item' in df_expenses.columns
        assert df_expenses.iloc[0]['Item'] == 'Lunch'
        assert df_expenses.iloc[0]['Amount'] == 100.0
        assert df_expenses.iloc[0]['Paid By'] == 'Alice'

# Note: GUI and Kivy-specific logic in main.py is not covered by these tests.
# For full coverage, consider using Kivy's test framework or mocking UI components.
