import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import NCMConverterGUI


def main():
    app = QApplication(sys.argv)
    window = NCMConverterGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
