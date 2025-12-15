# reset_password.py
import hashlib
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class ResetPasswordWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("Reset User Password")
        self.setGeometry(500, 300, 400, 200)

        layout = QVBoxLayout()

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password")

        btn = QPushButton("Reset Password")
        btn.clicked.connect(self.reset)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("New Password"))
        layout.addWidget(self.new_password)
        layout.addWidget(btn)

        self.setLayout(layout)

    def reset(self):
        hashed = hashlib.sha256(self.new_password.text().encode()).hexdigest()
        self.db.update(
            "LoginTbl",
            {"Password": hashed},
            "Username=?",
            (self.username.text(),)
        )
        QMessageBox.information(self, "Success", "Password reset successfully")
        self.close()
