# login.py
import sys
import os
import hashlib
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from db_manager import DBManager
from dashboard import Dashboard


class LoginWindow(QWidget):
    # Signal emitted after successful login
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SACCO Login")
        self.setGeometry(600, 300, 500, 320)
        self.db_manager = None
        self.db_path = ""
        self.init_ui()

    # ---------------- UI ----------------
    def init_ui(self):
        layout = QVBoxLayout()

        self.db_label = QLabel("Database: None selected")
        select_db_btn = QPushButton("Select Existing Database")
        select_db_btn.clicked.connect(self.select_database)
        layout.addWidget(self.db_label)
        layout.addWidget(select_db_btn)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)

        btns = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        create_btn = QPushButton("Create New User")
        create_btn.clicked.connect(self.create_user)
        btns.addWidget(login_btn)
        btns.addWidget(create_btn)
        layout.addLayout(btns)
        self.setLayout(layout)

    # ---------------- DATABASE ----------------
    def select_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Database", "", "Database Files (*.sld *.db *.sqlite)"
        )
        if not file_path:
            return
        self.db_path = os.path.abspath(file_path)
        self.db_label.setText(f"Database: {self.db_path}")
        self.db_manager = DBManager(self.db_path)
        self.ensure_login_table()
        QMessageBox.information(self, "Database Loaded", f"Loaded:\n{self.db_path}")

    def ensure_login_table(self):
        """Create LoginTbl if missing."""
        if "LoginTbl" not in self.db_manager.get_tables():
            self.db_manager.execute_query("""
                CREATE TABLE LoginTbl (
                    Username TEXT PRIMARY KEY,
                    Password TEXT NOT NULL,
                    Status TEXT,
                    Maintain INTEGER DEFAULT 0,
                    Operations INTEGER DEFAULT 0,
                    EditPriv INTEGER DEFAULT 0,
                    Reports INTEGER DEFAULT 0
                )
            """)

    # ---------------- AUTH ----------------
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def login(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Error", "Please select a database first.")
            return
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password.")
            return

        hashed = self.hash_password(password)
        users = self.db_manager.fetch_all("LoginTbl", "Username=? AND Password=?", (username, hashed))
        
        # Legacy plain-text support
        if not users:
            legacy = self.db_manager.fetch_all("LoginTbl", "Username=? AND Password=?", (username, password))
            if legacy:
                # Auto-upgrade password
                self.db_manager.update("LoginTbl", {"Password": hashed}, "Username=?", (username,))
                users = legacy

        if not users:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            return

        QMessageBox.information(self, "Success", f"Welcome {username}")
        # Emit signal instead of opening dashboard directly
        self.login_successful.emit(username)

    # ---------------- USER CREATION ----------------
    def create_user(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Error", "Please select a database first.")
            return
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return
        existing = self.db_manager.fetch_all("LoginTbl", "Username=?", (username,))
        if existing:
            QMessageBox.warning(self, "Error", "Username already exists.")
            return
        self.db_manager.insert("LoginTbl", {
            "Username": username,
            "Password": self.hash_password(password),
            "Status": "User",
            "Maintain": 0,
            "Operations": 0,
            "EditPriv": 0,
            "Reports": 0
        })
        QMessageBox.information(self, "Success", f"User '{username}' created successfully.")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
