# user_admin.py
import hashlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout,
    QMessageBox, QInputDialog
)
from reset_password import ResetPasswordWindow

class UserAdminWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("User Management")
        self.setGeometry(400, 200, 900, 500)

        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()

        # User table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_users)

        self.add_btn = QPushButton("Add User")
        self.add_btn.clicked.connect(self.add_user)

        self.delete_btn = QPushButton("Delete User")
        self.delete_btn.clicked.connect(self.delete_user)

        self.reset_btn = QPushButton("Reset Password")
        self.reset_btn.clicked.connect(self.reset_password)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # ---------------- USER TABLE ----------------
    def load_users(self):
        users = self.db.fetch_all("LoginTbl")
        if not users:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        self.table.setRowCount(len(users))
        self.table.setColumnCount(len(users[0]))
        self.table.setHorizontalHeaderLabels(users[0].keys())

        for r, row in enumerate(users):
            for c, k in enumerate(row.keys()):
                self.table.setItem(r, c, QTableWidgetItem(str(row[k])))
        self.table.resizeColumnsToContents()

    # ---------------- ADD / DELETE ----------------
    def add_user(self):
        username, ok1 = QInputDialog.getText(self, "Add User", "Enter username:")
        if not ok1 or not username.strip():
            return

        password, ok2 = QInputDialog.getText(self, "Add User", "Enter password:")
        if not ok2 or not password:
            return

        existing = self.db.fetch_all("LoginTbl", "Username=?", (username,))
        if existing:
            QMessageBox.warning(self, "Error", f"Username '{username}' already exists.")
            return

        hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.db.insert("LoginTbl", {
            "Username": username,
            "Password": hashed,
            "Status": "User",
            "Maintain": 0,
            "Operations": 0,
            "EditPriv": 0,
            "Reports": 0
        })
        QMessageBox.information(self, "Success", f"User '{username}' created successfully.")
        self.load_users()

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a user to delete.")
            return
        username = self.table.item(row, 0).text()
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Delete user '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete("LoginTbl", "Username=?", (username,))
            self.load_users()

    # ---------------- RESET PASSWORD ----------------
    def reset_password(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a user to reset password.")
            return
        username = self.table.item(row, 0).text()
        reset_window = ResetPasswordWindow(self.db)
        reset_window.username.setText(username)
        reset_window.show()
