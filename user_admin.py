# user_admin.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton

class UserAdminWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("User Management")
        self.setGeometry(400, 200, 700, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        layout.addWidget(self.table)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.load)
        layout.addWidget(refresh)

        self.setLayout(layout)
        self.load()

    def load(self):
        users = self.db.fetch_all("LoginTbl")
        self.table.setRowCount(len(users))
        self.table.setColumnCount(len(users[0]))
        self.table.setHorizontalHeaderLabels(users[0].keys())

        for r, row in enumerate(users):
            for c, k in enumerate(row.keys()):
                self.table.setItem(r, c, QTableWidgetItem(str(row[k])))
