# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from utils import get_project_root
from login import LoginWindow
from dashboard import Dashboard
from db_manager import DBManager


def setup_app() -> QApplication:
    """Initialize the QApplication with global settings and style."""
    app = QApplication(sys.argv)
    app.setApplicationName("SACCO Management App")

    # Global stylesheet
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

    # App icon
    icon_path = f"{get_project_root()}/assets/logo.png"
    try:
        app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"Warning: Could not load app icon. {e}")

    return app


def launch_dashboard(username: str):
    """Launch the dashboard after successful login."""
    db_path = f"{get_project_root()}/database/CooperativeDataBase.sld"
    window = Dashboard(db_path, username)
    window.show()
    return window


def main():
    app = setup_app()

    # Initialize login window
    login_window = LoginWindow()
    
    # On successful login, launch dashboard
    def on_login_success(username):
        login_window.close()
        launch_dashboard(username)

    login_window.login_successful.connect(on_login_success)
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
