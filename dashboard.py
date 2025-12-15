# dashboard.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget
)
from PyQt6.QtGui import QFont
from db_manager import DBManager
from table_form import TableForm  # Reusable form for add/edit records


class Dashboard(QMainWindow):
    def __init__(self, db_path, username):
        super().__init__()
        self.setWindowTitle(f"SACCO Dashboard - Logged in as {username}")
        self.setGeometry(400, 100, 1200, 700)
        self.db_manager = DBManager(db_path)

        # Keep track of loaded module widgets
        self.loaded_modules = {}

        # Map of modules to table names
        self.modules = {
            "Stations": "StationDB",
            "Members": "MemberDataTbl",
            "Account Types": "AccountTypesTbl",
            "Loans & Purchases": "LoansAndPurchasesTbl",
            "Transactions": "PayOrWithdrawTbl",
            "Ledger": "LedgerTbl"
        }

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Modules")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        sidebar.addWidget(title)

        # Dynamically create module buttons
        for module_name, table_name in self.modules.items():
            btn = QPushButton(module_name)
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda _, tn=table_name: self.load_module(tn))
            sidebar.addWidget(btn)

        sidebar.addStretch()
        main_layout.addLayout(sidebar)

        # Central stacked widget
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Default welcome page
        self.show_welcome_page()

    def show_welcome_page(self):
        welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_label = QLabel("Welcome to SACCO Management System")
        welcome_label.setFont(QFont("Arial", 20))
        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addStretch()
        welcome_page.setLayout(welcome_layout)
        self.stack.addWidget(welcome_page)
        self.stack.setCurrentWidget(welcome_page)

    def load_module(self, table_name):
        """Load a module into the central widget using TableForm"""
        try:
            # If already loaded, just show it
            if table_name in self.loaded_modules:
                self.stack.setCurrentWidget(self.loaded_modules[table_name])
                return

            # Check if table exists
            if table_name not in self.db_manager.get_tables():
                QMessageBox.warning(self, "Warning", f"Table '{table_name}' does not exist.")
                return

            # Create new module page
            module_page = QWidget()
            module_page.table_name = table_name
            layout = QVBoxLayout()
            module_page.setLayout(layout)

            # Module label
            label = QLabel(f"{table_name} Management")
            label.setFont(QFont("Arial", 18))
            layout.addWidget(label)

            # Add new record button
            entity_name = table_name.replace("Tbl", "").replace("DB", "")
            add_btn = QPushButton(f"Add New {entity_name}")
            add_btn.setFixedHeight(40)
            add_btn.clicked.connect(lambda _, tn=table_name: self.open_table_form(tn))
            layout.addWidget(add_btn)

            self.stack.addWidget(module_page)
            self.stack.setCurrentWidget(module_page)
            self.loaded_modules[table_name] = module_page

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load module:\n{str(e)}")

    def open_table_form(self, table_name, record=None):
        """Open the TableForm dialog for add/edit"""
        try:
            form = TableForm(self.db_manager, table_name, record)
            if form.exec():
                QMessageBox.information(self, "Success", f"{table_name} updated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open form:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_path = "C:/path/to/CooperativeDataBase.sld"  # <-- Replace with actual path
    window = Dashboard(db_path, "okiemute")
    window.show()
    sys.exit(app.exec())
