from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QFrame
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import os


class WelcomeWindow(QMainWindow):
    def __init__(self):
        # Додайте цей рядок, щоб викликати конструктор батьківського класу
        super().__init__()

        self.setWindowTitle("Passlama")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: #1E1E2E;")

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        central_widget.setLayout(layout)

        self.add_title(layout, "Passlama", 24, "#FFFFFF")
        self.add_subtitle(layout, "WEB3", "#6C5CE7")
        self.add_divider(layout)
        self.add_title(layout, "PASSWORD MANAGER", 16, "#FFFFFF")
        self.add_connect_button(layout)

    def add_title(self, layout, text, font_size, color):
        title = QLabel(text)
        title.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {color};")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

    def add_subtitle(self, layout, text, color):
        subtitle = QLabel(text)
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet(f"color: {color};")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

    def add_divider(self, layout):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #3A3A4A;")
        divider.setFixedWidth(200)
        layout.addWidget(divider, alignment=Qt.AlignmentFlag.AlignCenter)

    def add_connect_button(self, layout):
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5D4ACF;
            }
        """)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.connect_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def load_styles(self):
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        with open(style_path, "r") as file:
            self.setStyleSheet(file.read())
