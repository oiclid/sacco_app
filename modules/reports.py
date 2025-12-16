# modules/reports.py
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from fpdf import FPDF
import pandas as pd
from db_manager import DBManager


class ReportsModule:
    """
    Reports Module
    - View tables in a tabular format
    - Export to CSV or PDF
    - Can integrate with dashboard filters
    """

    def __init__(self, db: DBManager):
        self.db = db

    # ---------------- VIEW TABLE ----------------
    def view_table(self, table_name: str, parent=None):
        data = self.db.fetch_all(table_name)
        if not data:
            QMessageBox.information(parent, "Empty", f"No data available in {table_name}.")
            return

        page = QWidget(parent)
        layout = QVBoxLayout(page)

        table_widget = QTableWidget()
        table_widget.setSortingEnabled(True)
        table_widget.setAlternatingRowColors(True)
        layout.addWidget(table_widget)

        self.populate_table(table_widget, data)

        # Export buttons
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        btn_layout = QHBoxLayout()
        export_csv_btn = QPushButton("Export CSV", clicked=lambda: self.export_csv(table_widget))
        export_pdf_btn = QPushButton("Export PDF", clicked=lambda: self.export_pdf(table_widget))
        btn_layout.addWidget(export_csv_btn)
        btn_layout.addWidget(export_pdf_btn)
        layout.addLayout(btn_layout)

        page.setLayout(layout)
        page.setWindowTitle(f"Report: {table_name}")
        page.resize(1000, 600)
        page.show()
        return page

    # ---------------- POPULATE TABLE ----------------
    def populate_table(self, table: QTableWidget, data: list[dict]):
        table.clear()
        if not data:
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        headers = list(data[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(data))

        for r, row in enumerate(data):
            for c, h in enumerate(headers):
                item = QTableWidgetItem(str(row[h]))
                table.setItem(r, c, item)
        table.resizeColumnsToContents()

    # ---------------- EXPORT CSV ----------------
    def export_csv(self, table: QTableWidget):
        path, _ = QFileDialog.getSaveFileName(None, "Export CSV", "", "*.csv")
        if not path:
            return
        df = pd.DataFrame([[table.item(r, c).text() for c in range(table.columnCount())]
                           for r in range(table.rowCount())],
                          columns=[table.horizontalHeaderItem(c).text() for c in range(table.columnCount())])
        try:
            df.to_csv(path, index=False)
            QMessageBox.information(None, "Exported", f"CSV exported successfully to {path}")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    # ---------------- EXPORT PDF ----------------
    def export_pdf(self, table: QTableWidget):
        path, _ = QFileDialog.getSaveFileName(None, "Export PDF", "", "*.pdf")
        if not path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        col_width = pdf.w / table.columnCount() - 1
        row_height = 8

        # Headers
        for c in range(table.columnCount()):
            pdf.cell(col_width, row_height, table.horizontalHeaderItem(c).text(), border=1)
        pdf.ln(row_height)

        # Rows
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                pdf.cell(col_width, row_height, table.item(r, c).text(), border=1)
            pdf.ln(row_height)

        try:
            pdf.output(path)
            QMessageBox.information(None, "Exported", f"PDF exported successfully to {path}")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
