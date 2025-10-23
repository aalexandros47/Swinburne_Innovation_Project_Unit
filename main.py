from PyQt6.QtWidgets import QApplication
import sys
from ui_main import MainUI

def main():
    app = QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
