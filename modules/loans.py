# modules/loans.py
from datetime import date, timedelta
from PyQt6.QtWidgets import QMessageBox
from db_manager import DBManager
from table_form import TableForm


class LoansModule:
    """
    Loans Module with:
    - Flat-rate loans (current default)
    - Future-ready reducing-balance loans
    - Admin-editable loan products
    - Repayment schedules
    - Approval workflow (Pending → Approved → Disbursed)
    - Ledger auto-posting
    """

    LOANS_TABLE = "LoansTbl"
    SCHEDULE_TABLE = "LoanRepaymentScheduleTbl"
    LOAN_TYPES_TABLE = "LoanTypesTbl"
    LEDGER_TABLE = "LedgerTbl"

    def __init__(self, db: DBManager):
        self.db = db
        self.ensure_tables()
        self.seed_default_loan_types()

    # --------------------------------------------------
    # DATABASE SETUP
    # --------------------------------------------------
    def ensure_tables(self):
        if self.LOAN_TYPES_TABLE not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.LOAN_TYPES_TABLE} (
                    LoanTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
                    LoanName TEXT UNIQUE NOT NULL,
                    InterestRate REAL NOT NULL,
                    DurationMonths INTEGER NOT NULL,
                    Active INTEGER DEFAULT 1
                )
            """)

        if self.LOANS_TABLE not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.LOANS_TABLE} (
                    LoanID INTEGER PRIMARY KEY AUTOINCREMENT,
                    MemberID TEXT NOT NULL,
                    LoanType TEXT NOT NULL,
                    LoanAmount REAL NOT NULL,
                    InterestRate REAL NOT NULL,
                    DurationMonths INTEGER NOT NULL,
                    StartDate TEXT NOT NULL,
                    TotalPayable REAL,
                    Status TEXT DEFAULT 'Active',
                    ApprovalStatus TEXT DEFAULT 'Pending',
                    DisbursementDate TEXT,
                    LoanMethod TEXT DEFAULT 'Flat'
                )
            """)

        if self.SCHEDULE_TABLE not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.SCHEDULE_TABLE} (
                    ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
                    LoanID INTEGER NOT NULL,
                    DueDate TEXT NOT NULL,
                    Principal REAL NOT NULL,
                    Interest REAL NOT NULL,
                    AmountDue REAL NOT NULL,
                    AmountPaid REAL DEFAULT 0,
                    Status TEXT DEFAULT 'Pending',
                    FOREIGN KEY (LoanID) REFERENCES {self.LOANS_TABLE}(LoanID)
                )
            """)

        if self.LEDGER_TABLE not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.LEDGER_TABLE} (
                    EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Date TEXT NOT NULL,
                    Account TEXT NOT NULL,
                    Debit REAL DEFAULT 0,
                    Credit REAL DEFAULT 0,
                    Description TEXT
                )
            """)

    # --------------------------------------------------
    # DEFAULT LOAN PRODUCTS (ADMIN EDITABLE)
    # --------------------------------------------------
    def seed_default_loan_types(self):
        defaults = [
            ("Major", 10, 24),
            ("Car", 15, 36),
            ("Electronics", 10, 18),
            ("Land", 10, 24),
            ("Essential Commodities", 10, 12),
            ("Education", 10, 6),
            ("Emergency", 5, 4),
        ]

        existing = {r["LoanName"] for r in self.db.fetch_all(self.LOAN_TYPES_TABLE)}

        for name, rate, months in defaults:
            if name not in existing:
                self.db.insert(self.LOAN_TYPES_TABLE, {
                    "LoanName": name,
                    "InterestRate": rate,
                    "DurationMonths": months,
                    "Active": 1
                })

    # --------------------------------------------------
    # LOAN CREATION
    # --------------------------------------------------
    def create_loan(self, loan_data: dict):
        """
        loan_data:
        - MemberID
        - LoanType
        - LoanAmount
        - StartDate
        - LoanMethod (Flat | Reduce)  [Reduce is future-ready]
        """

        loan_method = loan_data.get("LoanMethod", "Flat")

        product = self.db.fetch_all(
            self.LOAN_TYPES_TABLE,
            "LoanName=? AND Active=1",
            (loan_data["LoanType"],)
        )
        if not product:
            QMessageBox.warning(None, "Error", "Invalid or inactive loan type.")
            return

        product = product[0]
        principal = float(loan_data["LoanAmount"])
        rate = float(product["InterestRate"]) / 100
        months = int(product["DurationMonths"])

        if loan_method == "Flat":
            total_interest = principal * rate * (months / 12)
        else:  # Reduce-balance (future use)
            total_interest = sum(
                (principal - (principal / months) * i) * rate / 12
                for i in range(months)
            )

        total_payable = principal + total_interest

        loan_id = self.db.insert(self.LOANS_TABLE, {
            "MemberID": loan_data["MemberID"],
            "LoanType": loan_data["LoanType"],
            "LoanAmount": principal,
            "InterestRate": product["InterestRate"],
            "DurationMonths": months,
            "StartDate": loan_data["StartDate"],
            "TotalPayable": round(total_payable, 2),
            "ApprovalStatus": "Pending",
            "LoanMethod": loan_method
        })

        self.generate_schedule(
            loan_id, principal, rate, months,
            loan_data["StartDate"], loan_method
        )

        QMessageBox.information(
            None,
            "Loan Created",
            f"Loan created successfully\nTotal Payable: {total_payable:,.2f}"
        )

    # --------------------------------------------------
    # REPAYMENT SCHEDULE
    # --------------------------------------------------
    def generate_schedule(self, loan_id, principal, rate, months, start_date, method):
        start = date.fromisoformat(start_date)
        monthly_principal = principal / months
        remaining = principal

        for i in range(months):
            if method == "Flat":
                interest = (principal * rate) / months
            else:  # Reduce-balance
                interest = remaining * rate / 12

            amount_due = monthly_principal + interest
            due_date = start + timedelta(days=30 * (i + 1))

            self.db.insert(self.SCHEDULE_TABLE, {
                "LoanID": loan_id,
                "DueDate": due_date.isoformat(),
                "Principal": round(monthly_principal, 2),
                "Interest": round(interest, 2),
                "AmountDue": round(amount_due, 2)
            })

            remaining -= monthly_principal

    # --------------------------------------------------
    # APPROVAL / DISBURSEMENT
    # --------------------------------------------------
    def approve_loan(self, loan_id, permissions):
        if not permissions.get("Approve", 0):
            QMessageBox.warning(None, "Denied", "Approval permission required.")
            return
        self.db.update(self.LOANS_TABLE,
                       {"ApprovalStatus": "Approved"},
                       "LoanID=?", (loan_id,))

    def disburse_loan(self, loan_id, permissions):
        if not permissions.get("Disburse", 0):
            QMessageBox.warning(None, "Denied", "Disbursement permission required.")
            return
        self.db.update(self.LOANS_TABLE, {
            "ApprovalStatus": "Disbursed",
            "DisbursementDate": date.today().isoformat()
        }, "LoanID=?", (loan_id,))

    # --------------------------------------------------
    # PAYMENTS + LEDGER
    # --------------------------------------------------
    def record_payment(self, schedule_id, amount):
        row = self.db.fetch_all(
            self.SCHEDULE_TABLE, "ScheduleID=?", (schedule_id,)
        )[0]

        paid = row["AmountPaid"] + amount
        status = "Paid" if paid >= row["AmountDue"] else "Partial"

        self.db.update(self.SCHEDULE_TABLE, {
            "AmountPaid": paid,
            "Status": status
        }, "ScheduleID=?", (schedule_id,))

        self.db.insert(self.LEDGER_TABLE, {
            "Date": date.today().isoformat(),
            "Account": "Cash",
            "Debit": amount,
            "Credit": 0,
            "Description": f"Loan repayment Schedule {schedule_id}"
        })

        self.db.insert(self.LEDGER_TABLE, {
            "Date": date.today().isoformat(),
            "Account": "Loan Receivable",
            "Debit": 0,
            "Credit": amount,
            "Description": f"Loan repayment Schedule {schedule_id}"
        })

    # --------------------------------------------------
    # BALANCE & ARREARS
    # --------------------------------------------------
    def get_loan_balance(self, loan_id):
        rows = self.db.fetch_all(self.SCHEDULE_TABLE, "LoanID=?", (loan_id,))
        balance = sum(r["AmountDue"] - r["AmountPaid"] for r in rows)
        arrears = sum(
            r["AmountDue"] - r["AmountPaid"]
            for r in rows
            if r["DueDate"] < date.today().isoformat()
            and r["AmountPaid"] < r["AmountDue"]
        )
        return balance, arrears

    # --------------------------------------------------
    # ADMIN / UI
    # --------------------------------------------------
    def open_loan_types_admin(self, parent=None):
        TableForm(self.db, self.LOAN_TYPES_TABLE, parent).exec()

    def open_loan_form(self, parent=None):
        TableForm(self.db, self.LOANS_TABLE, parent, on_submit=self.create_loan).exec()

    def open_schedule_view(self, loan_id, parent=None):
        TableForm(
            self.db,
            self.SCHEDULE_TABLE,
            parent,
            where_clause="LoanID=?",
            where_args=(loan_id,)
        ).exec()
