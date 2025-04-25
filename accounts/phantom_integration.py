import json
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QUrl, pyqtSignal, QObject


class PhantomBridge(QObject):
    wallet_connected = pyqtSignal(str)  # Сигнал з публічним ключем


class PhantomWalletManager:
    def __init__(self, web_view: QWebEngineView):
        self.bridge = PhantomBridge()
        self.web_view = web_view
        self._setup_phantom_js()

    def _setup_phantom_js(self):
        # Ін'єкція JavaScript для роботи з Phantom
        js_code = """
        window.solana = window.solana || window.phantom?.solana;
        window.solanaBridge = {
            connect: async function() {
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
        };
        true;  // Повертаємо true для успішного виконання
        """
        self.web_view.page().runJavaScript(js_code)

    def connect(self):
        # Виклик JavaScript-функції через QWebEngineView
        self.web_view.page().runJavaScript(
            "window.solanaBridge.connect()",
            lambda result: self._handle_connect_result(result)
        )

    def _handle_connect_result(self, result):
        try:
            if isinstance(result, str):
                result = json.loads(result)

            if result.get("error"):
                QMessageBox.critical(None, "Помилка", result["error"])
            elif result.get("publicKey"):
                self.bridge.wallet_connected.emit(result["publicKey"])
        except Exception as e:
            QMessageBox.critical(None, "Помилка", f"Помилка обробки: {str(e)}")
