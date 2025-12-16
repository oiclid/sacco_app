# modules/stations.py
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from table_form import TableForm
from db_manager import DBManager


class StationsModule:
    """
    Stations Module
    - Add / Edit / Delete stations
    - Provides UI integration with TableForm
    """

    STATIONS_TABLE = "StationDB"

    def __init__(self, db: DBManager):
        self.db = db
        self.ensure_table()

    # ---------------- DATABASE ----------------
    def ensure_table(self):
        """Create the stations table if it doesn't exist."""
        if self.STATIONS_TABLE not in self.db.get_tables():
            self.db.execute_query(f"""
                CREATE TABLE {self.STATIONS_TABLE} (
                    StationID INTEGER PRIMARY KEY AUTOINCREMENT,
                    StationName TEXT UNIQUE NOT NULL,
                    Location TEXT,
                    Description TEXT
                )
            """)

    # ---------------- CRUD ----------------
    def add_station(self, station_data: dict):
        """
        station_data: {"StationName": str, "Location": str, "Description": str}
        """
        try:
            self.db.insert(self.STATIONS_TABLE, station_data)
            QMessageBox.information(None, "Success", f"Station '{station_data['StationName']}' added.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def edit_station(self, station_id: int, updates: dict):
        """
        updates: {"StationName": str, "Location": str, "Description": str}
        """
        try:
            self.db.update(self.STATIONS_TABLE, updates, "StationID=?", (station_id,))
            QMessageBox.information(None, "Success", f"Station ID {station_id} updated.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def delete_station(self, station_id: int):
        confirm = QMessageBox.question(
            None,
            "Confirm Delete",
            f"Are you sure you want to delete Station ID {station_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete(self.STATIONS_TABLE, "StationID=?", (station_id,))
                QMessageBox.information(None, "Deleted", f"Station ID {station_id} deleted.")
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))

    # ---------------- UI ----------------
    def open_stations_admin(self, parent=None):
        """
        Open a TableForm for Stations management
        Allows Add/Edit/Delete directly from the form
        """
        form = TableForm(
            db=self.db,
            table_name=self.STATIONS_TABLE,
            parent=parent
        )
        form.exec()
