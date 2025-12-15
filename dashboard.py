# dashboard.py (enhanced with UserAdmin integration)
import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate

from db_manager import DBManager
from table_form import TableForm
from user_admin import UserAdminWindow

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import pandas as pd
from fpdf import FPDF


class Dashboard(QMainWindow):
    def __init__(self, db_path, username):
        super().__init__()
        self.setWindowTitle(f"SACCO Dashboard — Logged in as {username}")
        self.setGeometry(300, 100, 1600, 950)

        self.db_manager = DBManager(db_path)
        self.loaded_modules = {}
        self.column_filters = {}

        self.modules_friendly = {
            "StationDB": "Stations",
            "MemberDataTbl": "Members",
            "AccountTypesTbl": "Account Types",
            "LoansAndPurchasesTbl": "Loans & Purchases",
            "PayOrWithdrawTbl": "Transactions",
            "LedgerTbl": "Ledger",
            "UserAdmin": "User Management"  # new admin module
        }

        self.categories = {
            "Accounts": ["AccountTypesTbl"],
            "Members": ["MemberDataTbl"],
            "Operations": ["StationDB", "LoansAndPurchasesTbl", "PayOrWithdrawTbl"],
            "Finance": ["LedgerTbl"],
            "Admin": ["UserAdmin"]  # admin category
        }

        self.init_ui()
        self.apply_styles()

    # ---------------- UI SETUP ----------------
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(sidebar_container)
        scroll.setWidget(sidebar_container)
        main_layout.addWidget(scroll, 1)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 4)

        self.build_sidebar()
        self.show_welcome_page()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f4f6f8; }
            QLabel { color: #2c3e50; }
            QPushButton { font-weight: bold; }
            QTableWidget { background-color: white; alternate-background-color: #f9f9f9; }
        """)

    # ---------------- SIDEBAR ----------------
    def build_sidebar(self):
        while self.sidebar_layout.count():
            w = self.sidebar_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        title = QLabel("Modules", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.sidebar_layout.addWidget(title)

        for category, tables in self.categories.items():
            cat = QLabel(category)
            cat.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            cat.setStyleSheet("color:#1f77b4;")
            self.sidebar_layout.addWidget(cat)

            for table in tables:
                # For database tables, check existence; for admin modules, allow directly
                if table != "UserAdmin" and table not in self.db_manager.get_tables():
                    continue
                btn = QPushButton(self.modules_friendly.get(table, table))
                btn.setFixedHeight(40)
                btn.clicked.connect(lambda _, t=table: self.load_module(t))
                btn.setStyleSheet("""
                    QPushButton { background:#ffd8b1; border-radius:6px; }
                    QPushButton:hover { background:#ffb347; }
                """)
                self.sidebar_layout.addWidget(btn)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            self.sidebar_layout.addWidget(line)

        self.sidebar_layout.addStretch()

    # ---------------- MODULE LOADING ----------------
    def load_module(self, table_name):
        # Admin module: open in separate window
        if table_name == "UserAdmin":
            self.user_admin_window = UserAdminWindow(self.db_manager)
            self.user_admin_window.show()
            return

        if table_name in self.loaded_modules:
            self.stack.setCurrentWidget(self.loaded_modules[table_name])
            return

        data = self.db_manager.fetch_all(table_name)
        if not data:
            QMessageBox.warning(self, "Empty", "No data available.")
            return

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(f"{self.modules_friendly.get(table_name, table_name)} Management")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        filter_layout = QHBoxLayout()
        text_filter = QLineEdit()
        text_filter.setPlaceholderText("Global search...")
        chart_type = QComboBox()
        chart_type.addItems(["Line", "Bar", "Pie"])
        filter_layout.addWidget(text_filter)
        filter_layout.addWidget(chart_type)
        layout.addLayout(filter_layout)

        add_btn = QPushButton("Add New Record")
        add_btn.clicked.connect(lambda: self.open_table_form(table_name))
        layout.addWidget(add_btn)

        table = QTableWidget()
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)

        filter_controls = self.build_column_filters(data, table, table_name)
        layout.addLayout(filter_controls)

        canvas = FigureCanvas(Figure(figsize=(6, 3)))
        ax = canvas.figure.subplots()
        layout.addWidget(canvas)

        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Refresh", clicked=lambda: self.refresh(table, ax, table_name)))
        btns.addWidget(QPushButton("Export CSV", clicked=lambda: self.export_csv(table)))
        btns.addWidget(QPushButton("Export PDF", clicked=lambda: self.export_pdf(table)))
        layout.addLayout(btns)

        text_filter.textChanged.connect(lambda t: self.apply_filters(table, ax, table_name, t, chart_type))
        chart_type.currentTextChanged.connect(lambda _: self.apply_filters(table, ax, table_name, text_filter.text(), chart_type))

        self.populate_table(table, data)
        self.update_chart(ax, data, chart_type.currentText())

        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.loaded_modules[table_name] = page

    # ---------------- FILTERS / TABLE / CHART / EXPORT / UTILS ----------------
    def build_column_filters(self, data, table, table_name):
        layout = QHBoxLayout()
        self.column_filters[table_name] = {}
        for col, sample in data[0].items():
            box = QVBoxLayout()
            box.addWidget(QLabel(col))

            if isinstance(sample, int):
                mn, mx = QSpinBox(), QSpinBox()
                mx.setMaximum(10**12)
            elif isinstance(sample, float):
                mn, mx = QDoubleSpinBox(), QDoubleSpinBox()
                mx.setMaximum(10**12)
            elif self.is_date(sample):
                mn, mx = QDateEdit(), QDateEdit()
                mn.setCalendarPopup(True)
                mx.setCalendarPopup(True)
                mn.setDate(QDate(2000, 1, 1))
                mx.setDate(QDate.currentDate())
            else:
                continue

            for w in (mn, mx):
                if isinstance(w, (QSpinBox, QDoubleSpinBox)):
                    w.valueChanged.connect(lambda _, t=table_name: self.apply_filters(table, None, t))
                elif isinstance(w, QDateEdit):
                    w.dateChanged.connect(lambda _, t=table_name: self.apply_filters(table, None, t))

            box.addWidget(mn)
            box.addWidget(mx)
            layout.addLayout(box)
            self.column_filters[table_name][col] = (mn, mx)
        return layout

    def apply_filters(self, table, ax, table_name, text="", chart_type=None):
        data = self.db_manager.fetch_all(table_name)
        df = pd.DataFrame(data)
        if text:
            df = df[df.apply(lambda r: r.astype(str).str.contains(text, case=False).any(), axis=1)]
        for col, (mn, mx) in self.column_filters.get(table_name, {}).items():
            if isinstance(mn, QSpinBox):
                df = df[(df[col] >= mn.value()) & (df[col] <= mx.value())]
            elif isinstance(mn, QDoubleSpinBox):
                df = df[(df[col] >= mn.value()) & (df[col] <= mx.value())]
            elif isinstance(mn, QDateEdit):
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df[(df[col] >= pd.to_datetime(mn.date().toPyDate())) &
                        (df[col] <= pd.to_datetime(mx.date().toPyDate()))]
        self.populate_table(table, df.to_dict("records"))
        if ax and chart_type:
            self.update_chart(ax, df.to_dict("records"), chart_type.currentText() if hasattr(chart_type, "currentText") else chart_type)

    def populate_table(self, table, data):
        table.clear()
        if not data:
            table.setRowCount(0)
            table.setColumnCount(0)
            return
        headers = list(data[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, h in enumerate(headers):
                table.setItem(r, c, QTableWidgetItem(str(row[h])))
        table.resizeColumnsToContents()

    def update_chart(self, ax, data, chart_type):
        ax.clear()
        if not data:
            ax.figure.canvas.draw()
            return
        df = pd.DataFrame(data)
        nums = df.select_dtypes(include="number")
        if nums.empty:
            return
        if chart_type == "Line":
            nums.plot(ax=ax)
        elif chart_type == "Bar":
            nums.sum().plot(kind="bar", ax=ax)
        elif chart_type == "Pie":
            nums.sum().plot(kind="pie", ax=ax, autopct="%1.1f%%")
        ax.figure.canvas.draw()

    def export_csv(self, table):
        path, _ = QFileDialog.getSaveFileName(self, "CSV", "", "*.csv")
        if not path:
            return
        df = pd.DataFrame([[table.item(r, c).text() for c in range(table.columnCount())]
                           for r in range(table.rowCount())],
                          columns=[table.horizontalHeaderItem(c).text() for c in range(table.columnCount())])
        df.to_csv(path, index=False)

    def export_pdf(self, table):
        path, _ = QFileDialog.getSaveFileName(self, "PDF", "", "*.pdf")
        if not path:
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=9)
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                pdf.cell(40, 8, table.item(r, c).text(), 1)
            pdf.ln()
        pdf.output(path)

    def is_date(self, val):
        try:
            datetime.fromisoformat(str(val))
            return True
        except:
            return False

    def refresh(self, table, ax, table_name):
        self.apply_filters(table, ax, table_name)

    def open_table_form(self, table_name):
        form = TableForm(self.db_manager, table_name)
        form.exec()

    def show_welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        lbl = QLabel("Welcome to SACCO Dashboard")
        lbl.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_path = "C:/path/to/CooperativeDataBase.sld"
    window = Dashboard(db_path, "okiemute")
    window.show()
    sys.exit(app.exec())
