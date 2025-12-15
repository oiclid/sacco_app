# modules/members.py
from PyQt6.QtWidgets import QMessageBox
from table_form import TableForm
from db_manager import DBManager

class MembersModule:
    TABLE_NAME = "MemberDataTbl"

    def __init__(self, db_manager: DBManager):
        self.db = db_manager
        self.ensure_table_exists()

    def ensure_table_exists(self):
        """Create the members table if it doesn't exist."""
        if self.TABLE_NAME not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.TABLE_NAME} (
                    MemberID TEXT PRIMARY KEY,
                    FirstName TEXT NOT NULL,
                    MiddleName TEXT,
                    LastName TEXT NOT NULL,
                    Gender TEXT,
                    DateJoined TEXT,
                    StationID TEXT,
                    Phone TEXT,
                    Email TEXT
                )
            """)

    def fetch_all(self):
        """Fetch all members."""
        return self.db.fetch_all(self.TABLE_NAME)

    def add_member(self, member_data: dict):
        """Add a new member."""
        if "MemberID" not in member_data:
            member_data["MemberID"] = self.generate_member_id()
        try:
            self.db.insert(self.TABLE_NAME, member_data)
        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to add member: {e}")

    def edit_member(self, member_id: str, updated_data: dict):
        """Edit an existing member."""
        try:
            self.db.update(self.TABLE_NAME, updated_data, "MemberID=?", (member_id,))
        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to update member: {e}")

    def delete_member(self, member_id: str):
        """Delete a member."""
        confirm = QMessageBox.question(
            None,
            "Confirm Delete",
            f"Are you sure you want to delete Member ID {member_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete(self.TABLE_NAME, "MemberID=?", (member_id,))
            except Exception as e:
                QMessageBox.warning(None, "Error", f"Failed to delete member: {e}")

    def open_member_form(self, parent=None, member_data=None):
        """Open the TableForm for adding/editing a member."""
        form = TableForm(self.db, self.TABLE_NAME, data=member_data, parent=parent)
        form.exec()

    def generate_member_id(self):
        """Generate a unique MemberID based on existing members."""
        members = self.fetch_all()
        existing_ids = [m["MemberID"] for m in members if m.get("MemberID")]
        max_id = 0
        for mid in existing_ids:
            try:
                num = int(mid.replace("NFC", ""))
                if num > max_id:
                    max_id = num
            except:
                continue
        return f"NFC{max_id+1:03d}"
