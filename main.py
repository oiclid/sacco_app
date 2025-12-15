# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from utils import get_project_root
from login import LoginWindow


def setup_app() -> QApplication:
    """Initialize the QApplication with global settings and style."""
    app = QApplication(sys.argv)
    app.setApplicationName("SACCO Management App")

    # Optional: global stylesheet
    app.setStyleSheet("""
        QWidget { font-family: Arial; font-size: 12pt; }
        QPushButton { 
            background-color: #3498db; 
            color: white; 
            border-radius: 5px; 
            padding: 6px; 
        }
        QPushButton:hover { background-color: #2980b9; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox { padding: 4px; }
        QLabel { color: #2c3e50; }
    """)

    # Optional: app icon
    icon_path = f"{get_project_root()}/assets/logo.png"
    try:
        app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"Warning: Could not load app icon. {e}")

    return app


def main():
    app = setup_app()
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
