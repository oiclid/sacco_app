# reset_password.py
import hashlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QFont


class ResetPasswordWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("Reset User Password")
        self.setGeometry(500, 300, 400, 220)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Reset User Password")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username
        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username)

        # New Password
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Enter new password")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm new password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(QLabel("New Password"))
        layout.addWidget(self.new_password)
        layout.addWidget(QLabel("Confirm Password"))
        layout.addWidget(self.confirm_password)

        # Buttons
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Password")
        reset_btn.clicked.connect(self.reset_password)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def reset_password(self):
        username = self.username.text().strip()
        password = self.new_password.text()
        confirm = self.confirm_password.text()

        if not username or not password or not confirm:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        # Check if user exists
        user = self.db.fetch_one("LoginTbl", "Username=?", (username,))
        if not user:
            QMessageBox.warning(self, "Error", f"User '{username}' not found.")
            return

        hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.db.update("LoginTbl", {"Password": hashed}, "Username=?", (username,))

        QMessageBox.information(self, "Success", f"Password for '{username}' reset successfully!")
        self.close()
