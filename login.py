# login.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
)
from db_manager import DBManager  # Make sure this exists and handles SQLite connections


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SACCO Login")
        self.setGeometry(600, 300, 500, 300)
        self.db_manager = None
        self.db_path = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Database file info
        self.db_label = QLabel("Database: None selected")
        select_db_btn = QPushButton("Select Existing Database")
        select_db_btn.clicked.connect(self.select_database)
        layout.addWidget(self.db_label)
        layout.addWidget(select_db_btn)

        # Username and Password
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)

        # Buttons
        button_layout = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        create_btn = QPushButton("Create New User")
        create_btn.clicked.connect(self.create_user)
        button_layout.addWidget(login_btn)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def select_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database",
            "",
            "Database Files (*.sld *.db *.sqlite)"
        )
        if file_path:
            self.db_path = os.path.abspath(file_path)  # Full path
            self.db_label.setText(f"Database: {self.db_path}")
            self.db_manager = DBManager(self.db_path)
            QMessageBox.information(self, "Database Loaded", f"Loaded database:\n{self.db_path}")

    def login(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Error", "Please select a database first.")
            return
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password.")
            return

        users = self.db_manager.fetch_all(
            "LoginTbl", "Username=? AND Password=?", (username, password)
        )
        if users:
            QMessageBox.information(self, "Success", f"Login successful! Welcome {username}.")
            # TODO: Open Main Dashboard here
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password.")

    def create_user(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Error", "Please select a database first.")
            return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password.")
            return

        existing = self.db_manager.fetch_all("LoginTbl", "Username=?", (username,))
        if existing:
            QMessageBox.warning(self, "Error", "Username already exists.")
            return

        self.db_manager.insert("LoginTbl", {
            "Username": username,
            "Password": password,
            "Status": "User",
            "Maintain": "0",
            "Operations": "0",
            "EditPriv": "0",
            "Reports": "0"
        })
        QMessageBox.information(self, "Success", f"User '{username}' created successfully!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
