# dashboard.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from db_manager import DBManager
from table_form import TableForm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd


class Dashboard(QMainWindow):
    def __init__(self, db_path, username):
        super().__init__()
        self.setWindowTitle(f"SACCO Dashboard - Logged in as {username}")
        self.setGeometry(300, 100, 1500, 900)
        self.db_manager = DBManager(db_path)

        self.loaded_modules = {}
        self.modules_friendly = {
            "StationDB": "Stations",
            "MemberDataTbl": "Members",
            "AccountTypesTbl": "Account Types",
            "LoansAndPurchasesTbl": "Loans & Purchases",
            "PayOrWithdrawTbl": "Transactions",
            "LedgerTbl": "Ledger"
        }

        # Categories
        self.categories = {
            "Accounts": ["AccountTypesTbl"],
            "Members": ["MemberDataTbl"],
            "Operations": ["StationDB", "LoansAndPurchasesTbl", "PayOrWithdrawTbl"],
            "Finance": ["LedgerTbl"]
        }

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Sidebar
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout()
        sidebar_container.setLayout(self.sidebar_layout)
        scroll.setWidget(sidebar_container)
        main_layout.addWidget(scroll, 1)
        self.build_sidebar()

        # Central stacked widget
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 4)

        self.show_welcome_page()

    def build_sidebar(self):
        # Clear sidebar
        for i in reversed(range(self.sidebar_layout.count())):
            widget = self.sidebar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        title = QLabel("Modules", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.sidebar_layout.addWidget(title)

        for category, tables in self.categories.items():
            cat_label = QLabel(category)
            cat_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            cat_label.setStyleSheet("color: #1f77b4;")
            self.sidebar_layout.addWidget(cat_label)

            for table_name in tables:
                if table_name not in self.db_manager.get_tables():
                    continue
                display_name = self.modules_friendly.get(table_name, table_name)
                btn = QPushButton(display_name)
                btn.setFixedHeight(40)
                btn.clicked.connect(lambda _, tn=table_name: self.load_module(tn))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffcc99;
                        border: 1px solid #cc6600;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #ff9966;
                    }
                """)
                self.sidebar_layout.addWidget(btn)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            self.sidebar_layout.addWidget(line)

        self.sidebar_layout.addStretch()

    def add_category(self, category_name):
        if category_name in self.categories:
            QMessageBox.warning(self, "Warning", "Category already exists.")
            return
        self.categories[category_name] = []
        self.build_sidebar()

    def add_module_to_category(self, category_name, table_name):
        if category_name not in self.categories:
            QMessageBox.warning(self, "Warning", "Category does not exist.")
            return
        if table_name not in self.categories[category_name]:
            self.categories[category_name].append(table_name)
        self.build_sidebar()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QLabel { color: #333333; }
            QTableWidget { background-color: #ffffff; alternate-background-color: #f9f9f9; }
        """)

    def show_welcome_page(self):
        welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_label = QLabel("Welcome to SACCO Management System")
        welcome_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addStretch()
        welcome_page.setLayout(welcome_layout)
        self.stack.addWidget(welcome_page)
        self.stack.setCurrentWidget(welcome_page)

    def load_module(self, table_name):
        if table_name in self.loaded_modules:
            self.stack.setCurrentWidget(self.loaded_modules[table_name])
            return

        if table_name not in self.db_manager.get_tables():
            QMessageBox.warning(self, "Warning", f"Table '{table_name}' does not exist.")
            return

        module_page = QWidget()
        module_page.table_name = table_name
        layout = QVBoxLayout()
        module_page.setLayout(layout)

        display_name = self.modules_friendly.get(table_name, table_name)
        label = QLabel(f"{display_name} Management")
        label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(label)

        # Add record button
        add_btn = QPushButton(f"Add New {display_name.rstrip('s')}")
        add_btn.clicked.connect(lambda _, tn=table_name: self.open_table_form(tn))
        layout.addWidget(add_btn)

        # Table view
        table_widget = QTableWidget()
        table_widget.setAlternatingRowColors(True)
        table_widget.setSortingEnabled(True)
        self.populate_table_widget(table_widget, table_name)
        table_widget.itemChanged.connect(lambda item, tn=table_name: self.inline_update(item, tn))
        layout.addWidget(table_widget)

        # Charts
        chart = FigureCanvas(Figure(figsize=(5, 3)))
        ax = chart.figure.subplots()
        self.update_chart(ax, table_name)
        layout.addWidget(chart)

        # Summary dashboard for Finance & Loans
        if table_name in ["LedgerTbl", "LoansAndPurchasesTbl"]:
            summary_canvas = FigureCanvas(Figure(figsize=(5, 2)))
            summary_ax = summary_canvas.figure.subplots()
            self.update_summary_chart(summary_ax, table_name)
            layout.addWidget(summary_canvas)

        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda _, tw=table_widget, ax=ax, tn=table_name: self.refresh_module(tw, ax, tn))
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(lambda _, tw=table_widget: self.export_table_csv(tw))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

        self.stack.addWidget(module_page)
        self.stack.setCurrentWidget(module_page)
        self.loaded_modules[table_name] = module_page

    def populate_table_widget(self, table_widget, table_name):
        data = self.db_manager.fetch_all(table_name)
        if not data:
            table_widget.setRowCount(0)
            table_widget.setColumnCount(0)
            return
        headers = list(data[0].keys())
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        table_widget.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, key in enumerate(headers):
                table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(row[key])))
        table_widget.resizeColumnsToContents()

    def refresh_module(self, table_widget, ax, table_name):
        self.populate_table_widget(table_widget, table_name)
        self.update_chart(ax, table_name)

    def update_chart(self, ax, table_name):
        ax.clear()
        data = self.db_manager.fetch_all(table_name)
        if data:
            numeric_cols = [k for k, v in data[0].items() if isinstance(v, (int, float))]
            if numeric_cols:
                x = list(range(1, len(data)+1))
                for col in numeric_cols:
                    y = [row[col] for row in data]
                    ax.plot(x, y, marker='o', label=col)
                ax.set_title(f"Numeric Data Overview")
                ax.legend()
        ax.figure.canvas.draw()

    def update_summary_chart(self, ax, table_name):
        ax.clear()
        data = self.db_manager.fetch_all(table_name)
        if not data:
            return
        df = pd.DataFrame(data)
        if table_name == "LedgerTbl":
            # Example: Pie chart of debit vs credit
            if "Debit" in df.columns and "Credit" in df.columns:
                totals = [df["Debit"].sum(), df["Credit"].sum()]
                ax.pie(totals, labels=["Debit", "Credit"], autopct="%1.1f%%", colors=["#ff9999", "#66b3ff"])
                ax.set_title("Ledger Summary")
        elif table_name == "LoansAndPurchasesTbl":
            # Example: Bar chart by Loan Amount
            if "Amount" in df.columns:
                ax.bar(range(len(df)), df["Amount"], color="#99ff99")
                ax.set_title("Loans/Purchases Overview")
        ax.figure.canvas.draw()

    def export_table_csv(self, table_widget):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            df = pd.DataFrame([[table_widget.item(r, c).text() for c in range(table_widget.columnCount())] 
                               for r in range(table_widget.rowCount())],
                              columns=[table_widget.horizontalHeaderItem(c).text() 
                                       for c in range(table_widget.columnCount())])
            df.to_csv(path, index=False)
            QMessageBox.information(self, "Exported", f"Data exported to {path}")

    def open_table_form(self, table_name, record=None):
        try:
            form = TableForm(self.db_manager, table_name, record)
            if form.exec():
                QMessageBox.information(self, "Success", f"{table_name} updated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open form:\n{str(e)}")

    def inline_update(self, item: QTableWidgetItem, table_name):
        try:
            row = item.row()
            col_name = item.tableWidget().horizontalHeaderItem(item.column()).text()
            value = item.text()
            pk_col = item.tableWidget().horizontalHeaderItem(0).text()
            pk_value = item.tableWidget().item(row, 0).text()
            self.db_manager.update(table_name, {col_name: value}, f"{pk_col}=?", (pk_value,))
        except Exception as e:
            QMessageBox.warning(self, "Update Failed", f"Failed to update cell:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_path = "C:/path/to/CooperativeDataBase.sld"
    window = Dashboard(db_path, "okiemute")
    window.show()
    sys.exit(app.exec())
