# Data models for Expense Tracking App

class Participant:
    def __init__(self, name):
        self.name = name

class Expense:
    def __init__(self, item, amount, paid_by, omitted=None, notes=''):
        self.item = item
        self.amount = float(amount)
        self.paid_by = paid_by
        self.omitted = omitted if omitted else []
        self.notes = notes
