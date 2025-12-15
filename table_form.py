# table_form.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QMessageBox, QWidget, QFormLayout, QComboBox
)
from PyQt6.QtCore import QDate
from db_manager import DBManager
from datetime import datetime

class TableForm(QDialog):
    def __init__(self, db_manager: DBManager, table_name: str, record: dict = None):
        """
        Generic add/edit/delete form for any table.
        :param db_manager: Instance of DBManager
        :param table_name: Table name
        :param record: Optional existing record for editing
        """
        super().__init__()
        self.db_manager = db_manager
        self.table_name = table_name
        self.record = record
        self.setWindowTitle(f"{'Edit' if record else 'Add'} Record — {table_name}")
        self.setMinimumWidth(400)
        self.inputs = {}
        self.init_ui()
        self.populate_form()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # Fetch table columns
        self.columns = self.db_manager.get_columns(self.table_name)
        for col in self.columns:
            col_name = col["name"]
            col_type = col["type"].upper()
            not_null = col["not_null"]
            
            widget = self.create_widget_for_column(col_type)
            self.inputs[col_name] = widget
            self.form_layout.addRow(QLabel(f"{col_name} {'*' if not_null else ''}"), widget)

        self.layout.addLayout(self.form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_record)
        btn_layout.addWidget(self.save_btn)

        if self.record:
            self.delete_btn = QPushButton("Delete")
            self.delete_btn.clicked.connect(self.delete_record)
            btn_layout.addWidget(self.delete_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)

    def create_widget_for_column(self, col_type):
        """Return appropriate widget for a column type."""
        if "INT" in col_type:
            return QSpinBox()
        elif "REAL" in col_type or "FLOAT" in col_type:
            w = QDoubleSpinBox()
            w.setMaximum(1e12)
            return w
        elif "DATE" in col_type:
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())
            return date_edit
        elif "TEXT" in col_type:
            return QLineEdit()
        elif "CHAR" in col_type:
            combo = QComboBox()
            combo.addItems(["0", "1"])  # Example for boolean flags
            return combo
        else:
            return QLineEdit()  # Default fallback

    def populate_form(self):
        """If editing, fill in the current record."""
        if not self.record:
            return
        for col_name, widget in self.inputs.items():
            value = self.record.get(col_name)
            if value is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QDateEdit):
                try:
                    widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
                except:
                    widget.setDate(QDate.currentDate())
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)

    def validate_inputs(self):
        """Ensure required fields are filled."""
        for col in self.columns:
            col_name = col["name"]
            if col["not_null"]:
                widget = self.inputs[col_name]
                if isinstance(widget, QLineEdit) and not widget.text().strip():
                    return False, f"Field '{col_name}' is required."
        return True, ""

    def collect_data(self):
        """Return data dict ready for insert/update."""
        data = {}
        for col_name, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                data[col_name] = widget.text().strip()
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                data[col_name] = widget.value()
            elif isinstance(widget, QDateEdit):
                data[col_name] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QComboBox):
                data[col_name] = widget.currentText()
        return data

    def save_record(self):
        valid, msg = self.validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return
        data = self.collect_data()
        try:
            if self.record:
                # Update
                pk_col = self.columns[0]["name"]  # Assume first column is PK
                self.db_manager.update(self.table_name, data, f"{pk_col}=?", (self.record[pk_col],))
            else:
                # Insert
                self.db_manager.insert(self.table_name, data)
            QMessageBox.information(self, "Success", "Record saved successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_record(self):
        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                pk_col = self.columns[0]["name"]  # Assume first column is PK
                self.db_manager.delete(self.table_name, f"{pk_col}=?", (self.record[pk_col],))
                QMessageBox.information(self, "Deleted", "Record deleted successfully.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
