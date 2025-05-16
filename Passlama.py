import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedLayout, QHBoxLayout, QSizePolicy, QMenu,
    QLineEdit, QFormLayout, QFrame, QScrollArea, QListWidget, QListWidgetItem, QScroller, QScrollerProperties)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve


class AddPage(QWidget):
    def __init__(self, parent=None, edit_mode=False, site_data=None):
        super().__init__(parent)
        self.parent = parent
        self.edit_mode = edit_mode
        self.site_data = site_data
        self.setStyleSheet("""
            background-color: rgb(4, 52, 28);
            color: white;
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QWidget()
        header_layout = QHBoxLayout(header)

        self.back_button = QPushButton("←")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 24px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #aaa;
            }
        """)
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self.go_back)

        title = QLabel("Редагувати запис" if self.edit_mode else "Додати новий запис")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(title)
        header_layout.addStretch()

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 70, 48, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
            QLineEdit {
                background-color: rgb(22, 70, 48);
                color: white;
                border: 1px solid white;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
            QLabel {
                font-size: 16px;
                padding: 5px 0;
            }
        """)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)

        self.site_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        if self.edit_mode and self.site_data:
            self.site_input.setText(self.site_data['site'])
            self.password_input.setText(self.site_data['password'])

        form_layout.addRow("Сайт:", self.site_input)

        eye_layout = QHBoxLayout()
        eye_layout.addWidget(self.password_input)

        self.eye_button = QPushButton("👁️")
        self.eye_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 18px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #aaa;
            }
        """)
        self.eye_button.setFixedWidth(40)
        self.eye_button.clicked.connect(self.toggle_password_visibility)
        eye_layout.addWidget(self.eye_button)

        form_layout.addRow("Пароль:", eye_layout)

        generate_layout = QHBoxLayout()
        generate_layout.addStretch()

        self.generate_button = QPushButton("Згенерувати 🔑")
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(4, 128, 66, 0.7);
                color: white;
                font-size: 14px;
                border: 1px solid white;
                border-radius: 8px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(6, 150, 80, 0.8);
            }
        """)
        self.generate_button.setFixedHeight(30)
        generate_layout.addWidget(self.generate_button)

        form_layout.addRow(generate_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.cancel_button = QPushButton("Скасувати")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(100, 30, 30);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(120, 40, 40);
            }
        """)
        self.cancel_button.clicked.connect(self.go_back)

        self.save_button = QPushButton("Зберегти")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(4, 128, 66);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(6, 150, 80);
            }
        """)
        self.save_button.clicked.connect(self.save_data)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)

        layout.addWidget(header)
        layout.addWidget(form_frame)
        layout.addLayout(buttons_layout)
        layout.addStretch()

        self.setLayout(layout)

    def go_back(self):
        self.parent.stack_layout.setCurrentWidget(self.parent.main_screen)

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4CAF50;
                    font-size: 18px;
                    border: none;
                    padding: 5px;
                }
            """)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 18px;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    color: #aaa;
                }
            """)

    def save_data(self):
        site = self.site_input.text()
        password = self.password_input.text()

        if site and password:
            if self.edit_mode and self.site_data:
                # Find and update the existing site data
                for i, data in enumerate(self.parent.sites_data):
                    if data['site'] == self.site_data['site']:
                        # Update both site name and password
                        self.parent.sites_data[i]['site'] = site
                        self.parent.sites_data[i]['password'] = password
                        break
                self.parent.update_sites_list()
            else:
                self.parent.add_site_data(site, password)

            self.go_back()
            self.site_input.clear()
            self.password_input.clear()


class SiteDetailsPage(QWidget):
    def __init__(self, parent=None, site_data=None):
        super().__init__(parent)
        self.parent = parent
        self.site_data = site_data
        self.setStyleSheet("""
            background-color: rgb(4, 52, 28);
            color: white;
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QWidget()
        header_layout = QHBoxLayout(header)

        self.back_button = QPushButton("←")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 24px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #aaa;
            }
        """)
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self.go_back)

        title = QLabel(f"Дані для {self.site_data['site']}")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(title)
        header_layout.addStretch()

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 70, 48, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
            QLineEdit {
                background-color: rgb(22, 70, 48);
                color: white;
                border: 1px solid white;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
            QLabel {
                font-size: 16px;
                padding: 5px 0;
            }
        """)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)

        self.site_display = QLineEdit()
        self.site_display.setReadOnly(True)
        self.site_display.setStyleSheet("""
            QLineEdit {
                background-color: rgb(22, 70, 48);
                color: white;
                border: 1px solid white;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
        """)
        self.site_display.setText(self.site_data['site'])
        form_layout.addRow("Сайт:", self.site_display)

        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setStyleSheet("""
            QLineEdit {
                background-color: rgb(22, 70, 48);
                color: white;
                border: 1px solid white;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
        """)
        self.password_display.setText(self.site_data['password'])
        self.password_display.setEchoMode(QLineEdit.EchoMode.Password)

        self.eye_button = QPushButton("👁️")
        self.eye_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 18px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #aaa;
            }
        """)
        self.eye_button.clicked.connect(self.toggle_password_visibility)

        eye_layout = QHBoxLayout()
        eye_layout.addWidget(self.password_display)
        eye_layout.addWidget(self.eye_button)
        form_layout.addRow("Пароль:", eye_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.edit_button = QPushButton("Редагувати запис")
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(4, 128, 66);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(6, 150, 80);
            }
        """)
        self.edit_button.clicked.connect(self.edit_record)

        self.delete_button = QPushButton("Видалити запис")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(150, 30, 30);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(180, 40, 40);
            }
        """)
        self.delete_button.clicked.connect(self.delete_record)

        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)

        layout.addWidget(header)
        layout.addWidget(form_frame)
        layout.addLayout(buttons_layout)
        layout.addStretch()

        self.setLayout(layout)

    def go_back(self):
        self.parent.stack_layout.setCurrentWidget(self.parent.main_screen)

    def toggle_password_visibility(self):
        if self.password_display.echoMode() == QLineEdit.EchoMode.Password:
            self.password_display.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4CAF50;
                    font-size: 18px;
                    border: none;
                    padding: 5px;
                }
            """)
        else:
            self.password_display.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 18px;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    color: #aaa;
                }
            """)

    def edit_record(self):
        edit_page = AddPage(self.parent, edit_mode=True, site_data=self.site_data)
        self.parent.stack_layout.addWidget(edit_page)
        self.parent.stack_layout.setCurrentWidget(edit_page)

    def delete_record(self):
        for i, data in enumerate(self.parent.sites_data):
            if data['site'] == self.site_data['site']:
                del self.parent.sites_data[i]
                break

        self.parent.update_sites_list()
        self.go_back()


class AuthApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Passlama")
        self.setFixedSize(400, 640)
        self.setStyleSheet("background-color: rgb(4, 52, 28); color: white;")
        self.setWindowIcon(QIcon("icon.png"))
        self.sites_data = []

        self.stack_layout = QStackedLayout()
        self.setLayout(self.stack_layout)

        self.auth_screen = self.create_auth_screen()
        self.main_screen = self.create_main_screen()
        self.add_screen = AddPage(self)
        self.site_details_screen = None

        self.stack_layout.addWidget(self.auth_screen)
        self.stack_layout.addWidget(self.main_screen)
        self.stack_layout.addWidget(self.add_screen)

        self.stack_layout.setCurrentWidget(self.auth_screen)

    def create_auth_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()

        logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        middle_image = QLabel()
        middle_pixmap = QPixmap("logo_lama.PNG")
        middle_pixmap = middle_pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        middle_image.setPixmap(middle_pixmap)
        middle_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        connect_button = QPushButton("Connect Wallet")
        connect_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(4, 52, 28);
                color: white;
                font-size: 20px;
                font-family: 'Arial Rounded MT', sans-serif;
                padding: 12px 20px;
                border: 2px solid white;
                border-radius: 12px;
                text-shadow: 1px 1px 2px black;
                transition: all 0.3s ease-in-out;
            }
            QPushButton:hover {
                background-color: rgb(4, 128, 66);
                color: black;
                font-size: 19px;
            }
        """)
        connect_button.setFixedWidth(250)
        connect_button.clicked.connect(self.switch_to_main)

        layout.addSpacing(20)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(10)
        layout.addWidget(middle_image, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        layout.addWidget(connect_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(30)

        widget.setLayout(layout)
        return widget

    def create_main_screen(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(10)

        site_label = QLabel("Мої паролі")
        site_label.setStyleSheet("""
            font-size: 21px;
            font-family: 'Segoe UI', sans-serif;
            font-weight: bold;
            color: white;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 18px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            letter-spacing: 1.5px;
            text-shadow: 1px 1px 2px #000000;
        """)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.account_btn = QPushButton()
        self.account_btn.setIcon(QIcon("Profile.png"))
        self.account_btn.setIconSize(QSize(35, 35))
        self.account_btn.setFixedSize(48, 48)
        self.account_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid white;
                border-radius: 24px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.account_btn.clicked.connect(self.show_account_menu)

        top_layout.addWidget(site_label)
        top_layout.addWidget(spacer)
        top_layout.addWidget(self.account_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(top_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(22, 70, 48, 0.5);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.5);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroller = QScroller.scroller(scroll_area.viewport())
        scroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        properties = scroller.scrollerProperties()
        properties.setScrollMetric(QScrollerProperties.ScrollMetric.DragVelocitySmoothingFactor, 0.6)
        properties.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.001)
        properties.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.2)
        scroller.setScrollerProperties(properties)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)

        self.sites_list = QListWidget()
        self.sites_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(22, 70, 48, 0.7);
                border-radius: 15px;
                padding: 10px;
                font-size: 16px;
                color: white;
                border: 1px solid white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            QListWidget::item:hover {
                background-color: rgba(34, 100, 70, 0.7);
            }
            QListWidget::item:selected {
                background-color: rgb(34, 100, 70);
            }
        """)
        self.sites_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.sites_list.itemClicked.connect(self.show_site_details)

        self.sites_list.verticalScrollBar().valueChanged.connect(self.check_scroll_limits)

        container_layout.addWidget(self.sites_list)
        scroll_area.setWidget(container)

        main_layout.addWidget(scroll_area)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(48, 48)
        self.add_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid white;
                border-radius: 24px;
                background-color: transparent;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.add_btn.clicked.connect(self.show_add_menu)

        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 20, 20)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.add_btn)

        main_layout.addWidget(bottom_container)

        return widget

    def check_scroll_limits(self, value):
        scroll_bar = self.sites_list.verticalScrollBar()
        if value >= scroll_bar.maximum():
            self.animate_bounce_effect()
        elif value <= scroll_bar.minimum():
            self.animate_bounce_effect()

    def animate_bounce_effect(self):
        animation = QPropertyAnimation(self.sites_list, b"pos")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        start_pos = self.sites_list.pos()
        animation.setStartValue(start_pos)
        animation.setKeyValueAt(0.5, QPoint(start_pos.x(), start_pos.y() + 10))
        animation.setEndValue(start_pos)
        animation.start()

    def add_site_data(self, site, password):
        self.sites_data.append({
            'site': site,
            'password': password
        })
        self.update_sites_list()

    def update_sites_list(self):
        self.sites_list.clear()
        for i, site_data in enumerate(self.sites_data, 1):
            item = QListWidgetItem(f"{i}. {site_data['site']}")
            item.setData(Qt.ItemDataRole.UserRole, site_data)
            self.sites_list.addItem(item)

    def show_site_details(self, item):
        site_data = item.data(Qt.ItemDataRole.UserRole)
        self.site_details_screen = SiteDetailsPage(self, site_data)
        self.stack_layout.addWidget(self.site_details_screen)
        self.stack_layout.setCurrentWidget(self.site_details_screen)

    def show_account_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: rgb(22, 70, 48);
                color: white;
                border: 1px solid white;
                padding: 6px;
                font-size: 14px;
                min-width: 120px;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: rgb(34, 100, 70);
            }
        """)

        about_action = menu.addAction("Про акаунт")
        logout_action = menu.addAction("Log Out")
        logout_action.triggered.connect(self.logout)

        button_pos = self.account_btn.mapToGlobal(QPoint(0, 0))

        menu_pos = QPoint(
            button_pos.x() + self.account_btn.width() - menu.sizeHint().width(),
            button_pos.y() + self.account_btn.height()
        )

        menu.exec(menu_pos)

    def show_add_menu(self):
        self.stack_layout.setCurrentWidget(self.add_screen)

    def logout(self):
        self.stack_layout.setCurrentWidget(self.auth_screen)

    def switch_to_main(self):
        self.stack_layout.setCurrentWidget(self.main_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthApp()
    window.show()
    sys.exit(app.exec())