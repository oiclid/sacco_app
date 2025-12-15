# utils.py
import os
import shutil
from datetime import datetime
from typing import Any, List, Dict
import pandas as pd
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QWidget


# ---------------- PATH HELPERS ----------------
def get_project_root() -> str:
    """Return the absolute path to the project root."""
    return os.path.dirname(os.path.abspath(__file__))


def get_database_path(filename="CooperativeDataBase.sld") -> str:
    """Return full path to the database file."""
    return os.path.join(get_project_root(), "database", filename)


def ensure_folder(path: str):
    """Create folder if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


# ---------------- DATABASE BACKUP ----------------
def backup_database(db_path: str, backup_folder="backups") -> str:
    """Backup database to timestamped file in backup folder."""
    ensure_folder(os.path.join(get_project_root(), backup_folder))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(get_project_root(), backup_folder, f"Backup_{timestamp}.sld")
    shutil.copy(db_path, backup_file)
    return backup_file


# ---------------- VALIDATION HELPERS ----------------
def is_valid_username(username: str) -> bool:
    return username.isalnum() and 3 <= len(username) <= 20


def is_valid_password(password: str) -> bool:
    # Minimum 6 chars, at least 1 number and 1 letter
    if len(password) < 6:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    return has_letter and has_number


def show_message(widget: QWidget, title: str, text: str, msg_type="info"):
    """Show a standard message box."""
    if msg_type == "info":
        QMessageBox.information(widget, title, text)
    elif msg_type == "warning":
        QMessageBox.warning(widget, title, text)
    elif msg_type == "error":
        QMessageBox.critical(widget, title, text)


# ---------------- FILE EXPORT HELPERS ----------------
def export_dataframe_to_csv(df: pd.DataFrame, parent: QWidget, default_name="export.csv") -> str:
    path, _ = QFileDialog.getSaveFileName(parent, "Save CSV", default_name, "*.csv")
    if path:
        df.to_csv(path, index=False)
    return path


def export_dataframe_to_excel(df: pd.DataFrame, parent: QWidget, default_name="export.xlsx") -> str:
    path, _ = QFileDialog.getSaveFileName(parent, "Save Excel", default_name, "*.xlsx")
    if path:
        df.to_excel(path, index=False)
    return path


def export_dataframe_to_pdf(df: pd.DataFrame, parent: QWidget, default_name="export.pdf") -> str:
    from fpdf import FPDF

    path, _ = QFileDialog.getSaveFileName(parent, "Save PDF", default_name, "*.pdf")
    if not path:
        return ""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    col_widths = [40] * len(df.columns)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, col, 1)
    pdf.ln()

    for _, row in df.iterrows():
        for i, col in enumerate(df.columns):
            pdf.cell(col_widths[i], 8, str(row[col]), 1)
        pdf.ln()
    pdf.output(path)
    return path


# ---------------- DATA HELPERS ----------------
def dataframe_from_table(table_widget) -> pd.DataFrame:
    """Convert QTableWidget content to pandas DataFrame."""
    headers = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]
    data = []
    for row in range(table_widget.rowCount()):
        data.append([table_widget.item(row, col).text() for col in range(table_widget.columnCount())])
    return pd.DataFrame(data, columns=headers)


# ---------------- DATE HELPERS ----------------
def format_date(dt: datetime, fmt="%Y-%m-%d") -> str:
    return dt.strftime(fmt) if dt else ""


def parse_date(date_str: str, fmt="%Y-%m-%d") -> datetime:
    try:
        return datetime.strptime(date_str, fmt)
    except:
        return None


# ---------------- GENERIC UTILITIES ----------------
def chunk_list(lst: List[Any], n: int) -> List[List[Any]]:
    """Split a list into chunks of size n."""
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def safe_get(d: Dict, key: Any, default=None):
    """Safe dict get."""
    return d[key] if key in d else default
