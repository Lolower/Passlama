from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import os

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Passlama")
        self.setFixedSize(400, 600)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Лого
        logo = QLabel(self)
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "passlama_logo.jpg")
        pixmap = QPixmap(logo_path)
        logo.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Назва
        title = QLabel("Passlama")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("AppTitle")

        # Кнопка
        button = QPushButton("Увійти")
        button.setFixedHeight(40)
        button.setObjectName("EnterButton")

        layout.addWidget(logo)
        layout.addSpacing(20)
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(button)

        self.setLayout(layout)

        # Підключаємо стилі
        self.load_styles()

    def load_styles(self):
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        with open(style_path, "r") as file:
            self.setStyleSheet(file.read())
