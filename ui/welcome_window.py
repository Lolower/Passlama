from PyQt6.QtWidgets import QMessageBox, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QFrame
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import json
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"

class WelcomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.web_view = QWebEngineView()
        self.setWindowTitle("Passlama")
        self.setFixedSize(800, 600)

        self.init_ui()
        self.setup_phantom_js()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        central_widget.setLayout(layout)

        self.web_view.setVisible(False)
        layout.addWidget(self.web_view)

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

    def setup_phantom_js(self):
        js_code = """
           window.solana = window.solana || window.phantom?.solana;
           true;
           """
        self.web_view.page().runJavaScript(js_code)

    def connect_wallet(self):
        js_code = """
            async function connect() {
                try {
                    if (!window.solana || !window.solana.isPhantom) {
                        return { error: "Phantom Wallet not installed!" };
                    }
                    const response = await window.solana.connect();
                    return { publicKey: response.publicKey.toString() };
                } catch (err) {
                    return { error: err.message };
                }
            }
            connect();
            """

        self.web_view.page().runJavaScript(
            js_code,
            lambda result: self.handle_connect_result(result)
        )

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
        self.connect_btn.clicked.connect(self.connect_wallet)
        layout.addWidget(self.connect_btn, alignment=Qt.AlignmentFlag.AlignCenter)



def handle_connect_result(self, result):
    try:
        if isinstance(result, str):
            result = json.loads(result)

        if result.get("error"):
            QMessageBox.critical(self, "Error", result["error"])
        elif result.get("publicKey"):
            QMessageBox.information(self, "Success",
                                    f"Wallet connected!\nPublic Key: {result['publicKey']}")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")

