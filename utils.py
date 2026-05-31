# Utility functions for expense calculation
import pandas as pd
import os

def calculate_settlement(participants, expenses):
    balances = {p: 0 for p in participants}
    for exp in expenses:
        involved = [p for p in participants if p not in exp.omitted]
        share = exp.amount / len(involved)
        for p in involved:
            balances[p] -= share
        balances[exp.paid_by] += exp.amount
    return balances

def save_settlement_to_excel(trip_name, participants, expenses, balances, archive_dir):
    # Prepare summary data
    summary = []
    for p, bal in balances.items():
        if abs(bal) < 0.01:
            continue
        if bal > 0:
            summary.append({'Name': p, 'Type': 'Receive', 'Amount': round(bal, 2)})
        else:
            summary.append({'Name': p, 'Type': 'Pay', 'Amount': round(-bal, 2)})
    summary_df = pd.DataFrame(summary)

    # Prepare expenses data
    expenses_data = []
    for exp in expenses:
        expenses_data.append({
            'Item': exp.item,
            'Amount': exp.amount,
            'Paid By': exp.paid_by,
            'Omitted': ', '.join(exp.omitted) if exp.omitted else '',
            'Notes': getattr(exp, 'notes', '')
        })
    expenses_df = pd.DataFrame(expenses_data)

    # Save to Excel
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    file_path = os.path.join(archive_dir, f'{trip_name}.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        expenses_df.to_excel(writer, sheet_name='Expenses', index=False)
    return file_path

def load_trip_from_excel(file_path):
    df_summary = pd.read_excel(file_path, sheet_name='Summary')
    df_expenses = pd.read_excel(file_path, sheet_name='Expenses')
    return df_summary, df_expenses
