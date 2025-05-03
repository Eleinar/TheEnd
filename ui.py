import bcrypt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, 
                               QComboBox, QDialog, QLabel, QFormLayout, QDoubleSpinBox, QDateEdit,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QIcon, QPixmap
from sqlalchemy import func
from models import Session, User, RawMaterial, Recipe, Batch, FinishedProduct, Client, Order, OrderItem, UserRole, BatchStatus, ClientType, OrderStatus
from datetime import datetime
import matplotlib.pyplot as plt
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

APP_STYLE = """
    QWidget {
        background-color: #f5f5f5;
        color: #333333;
        font-family: Arial;
        font-size: 12px;
    }
    QPushButton {
        background-color: #e0e8f0;
        color: #333333;
        border: 1px solid #b0b0b0;
        padding: 6px 12px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #d0d8e0;
    }
    QPushButton:pressed {
        background-color: #c0c8d0;
    }
    QLineEdit, QDoubleSpinBox, QDateEdit, QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #b0b0b0;
        padding: 4px;
        border-radius: 2px;
    }
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #b0b0b0;
    }
    QTableWidget::item {
        background-color: #ffffff;
    }
    QTableWidget::item:nth-child(even) {
        background-color: #f0f0f0;
    }
    QTableWidget::item:selected {
        background-color: #d0e0f0;
        color: #333333;
    }
    QHeaderView::section {
        background-color: #e0e0e0;
        color: #333333;
        padding: 4px;
        border: 1px solid #b0b0b0;
    }
    QTabWidget::pane {
        border: 1px solid #b0b0b0;
    }
    QTabBar::tab {
        background-color: #e8e8e8;
        color: #333333;
        padding: 6px 12px;
        border: 1px solid #b0b0b0;
        border-bottom: none;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #333333;
        border-bottom: 2px solid #4682b4;
    }
    QLabel#notificationLabel {
        color: #008000;
        font-weight: bold;
    }
"""

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход")
        self.setFixedSize(300, 120)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        layout = QFormLayout()
        self.login_input = QLineEdit(self)
        self.login_input.setMaxLength(50)
        self.password_input = QLineEdit(self)
        self.password_input.setMaxLength(255)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Войти", self)
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.password_input)
        layout.addWidget(self.login_button)
        self.login_button.clicked.connect(self.validate_and_accept)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def validate_and_accept(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
    
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен содержать минимум 3 символа")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов")
            return
    
        user = self.session.query(User).filter_by(login=login).first()
        if not user:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return
    
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return
    
        self.user_id = user.user_id
        self.accept()

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить пользователя")
        self.setFixedSize(300, 200)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()

        layout = QFormLayout()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems([role.value for role in UserRole])

        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.password_input)
        layout.addRow("Роль:", self.role_combo)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Добавить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.create_button.clicked.connect(self.create_user)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def create_user(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен содержать минимум 3 символа")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов")
            return

        existing_user = self.session.query(User).filter_by(login=login).first()
        if existing_user:
            QMessageBox.warning(self, "Ошибка", "Логин уже занят")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(login=login, password=hashed_password.decode('utf-8'), role=role)
        self.session.add(user)
        self.session.commit()
        self.accept()

class EditUserDialog(QDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать пользователя")
        self.setFixedSize(300, 200)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.user_id = user_id
        self.user = self.session.query(User).filter_by(user_id=user_id).first()

        layout = QFormLayout()
        self.login_input = QLineEdit(self.user.login)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Оставьте пустым, чтобы не менять")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems([role.value for role in UserRole])
        self.role_combo.setCurrentText(self.user.role)

        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.password_input)
        layout.addRow("Роль:", self.role_combo)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.save_button.clicked.connect(self.save_user)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def save_user(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not login:
            QMessageBox.warning(self, "Ошибка", "Логин не может быть пустым")
            return
        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен содержать минимум 3 символа")
            return
        if password and len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов")
            return

        existing_user = self.session.query(User).filter(User.login == login, User.user_id != self.user_id).first()
        if existing_user:
            QMessageBox.warning(self, "Ошибка", "Логин уже занят")
            return

        self.user.login = login
        if password:
            self.user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.user.role = role
        self.session.commit()
        self.accept()

class AddRawMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить закупку")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()

        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 10000)
        self.quantity_spin.setValue(10)
        self.quantity_spin.setSuffix(" кг")
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10000)
        self.cost_spin.setValue(100)
        self.cost_spin.setSuffix(" руб/кг")
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())

        layout.addRow("Название:", self.name_input)
        layout.addRow("Количество:", self.quantity_spin)
        layout.addRow("Стоимость:", self.cost_spin)
        layout.addRow("Дата закупки:", self.purchase_date)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Добавить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.create_button.clicked.connect(self.create_raw_material)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def create_raw_material(self):
        name = self.name_input.text().strip()
        quantity = self.quantity_spin.value()
        cost = self.cost_spin.value()
        purchase_date = self.purchase_date.date().toString("yyyy-MM-dd")
        if not name or quantity < 0 or cost < 0:
            QMessageBox.warning(self, "Ошибка", "Заполните название, количество и стоимость корректно")
            return
        material = RawMaterial(name=name, quantity=quantity, cost=cost, purchase_date=purchase_date)
        self.session.add(material)
        self.session.commit()
        self.accept()

class EditRawMaterialDialog(QDialog):
    def __init__(self, parent=None, material_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать закупку")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.material = self.session.query(RawMaterial).filter_by(material_id=material_id).first()

        layout = QFormLayout()
        self.name_input = QLineEdit(self.material.name)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 10000)
        self.quantity_spin.setValue(self.material.quantity)
        self.quantity_spin.setSuffix(" кг")
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10000)
        self.cost_spin.setValue(self.material.cost)
        self.cost_spin.setSuffix(" руб/кг")
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.fromString(self.material.purchase_date, "yyyy-MM-dd"))

        layout.addRow("Название:", self.name_input)
        layout.addRow("Количество:", self.quantity_spin)
        layout.addRow("Стоимость:", self.cost_spin)
        layout.addRow("Дата закупки:", self.purchase_date)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.save_button.clicked.connect(self.save_material)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def save_material(self):
        name = self.name_input.text().strip()
        quantity = self.quantity_spin.value()
        cost = self.cost_spin.value()
        purchase_date = self.purchase_date.date().toString("yyyy-MM-dd")
        if not name or quantity < 0 or cost < 0:
            QMessageBox.warning(self, "Ошибка", "Заполните название, количество и стоимость корректно")
            return
        self.material.name = name
        self.material.quantity = quantity
        self.material.cost = cost
        self.material.purchase_date = purchase_date
        self.session.commit()
        self.accept()

class AddRecipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить рецепт")
        self.setFixedSize(350, 200)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()

        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.description_input = QLineEdit()

        layout.addRow("Название:", self.name_input)
        layout.addRow("Описание:", self.description_input)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Добавить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.create_button.clicked.connect(self.create_recipe)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def create_recipe(self):
        name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        if not name or not description:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        recipe = Recipe(name=name, description=description)
        self.session.add(recipe)
        self.session.commit()
        self.accept()

class EditRecipeDialog(QDialog):
    def __init__(self, parent=None, recipe_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать рецепт")
        self.setFixedSize(350, 200)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.recipe = self.session.query(Recipe).filter_by(recipe_id=recipe_id).first()

        layout = QFormLayout()
        self.name_input = QLineEdit(self.recipe.name)
        self.description_input = QLineEdit(self.recipe.description)

        layout.addRow("Название:", self.name_input)
        layout.addRow("Описание:", self.description_input)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.save_button.clicked.connect(self.save_recipe)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def save_recipe(self):
        name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        if not name or not description:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        self.recipe.name = name
        self.recipe.description = description
        self.session.commit()
        self.accept()

class CreateBatchDialog(QDialog):
    def __init__(self, parent=None, current_user_id=None):
        super().__init__(parent)
        self.setWindowTitle("Создать партию")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.current_user_id = current_user_id

        layout = QFormLayout()
        self.recipe_combo = QComboBox()
        recipes = self.session.query(Recipe).all()
        self.recipe_combo.addItems([r.name for r in recipes])
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(1, 1000)
        self.volume_spin.setValue(250)
        self.volume_spin.setSuffix(" л")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 10000)
        self.price_spin.setValue(500)
        self.price_spin.setSuffix(" руб/л")

        layout.addRow("Рецепт:", self.recipe_combo)
        layout.addRow("Объем:", self.volume_spin)
        layout.addRow("Дата начала:", self.start_date)
        layout.addRow("Цена за литр:", self.price_spin)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Создать")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.create_button.clicked.connect(self.create_batch)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def create_batch(self):
        recipe_name = self.recipe_combo.currentText()
        recipe = self.session.query(Recipe).filter_by(name=recipe_name).first()
        volume = self.volume_spin.value()
        price = self.price_spin.value()
        if not recipe or volume <= 0 or price < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите рецепт, объем > 0, цена >= 0")
            return

        honey = self.session.query(RawMaterial).filter_by(name="Мед").first()
        if not honey or honey.quantity < volume:
            QMessageBox.warning(self, "Ошибка", f"Недостаточно меда (нужно {volume} кг, есть {honey.quantity if honey else 0} кг)")
            return

        batch = Batch(
            recipe_id=recipe.recipe_id,
            volume=volume,
            start_date=self.start_date.date().toString("yyyy-MM-dd"),
            end_date=self.start_date.date().addDays(14).toString("yyyy-MM-dd"),
            status=BatchStatus.FERMENTING.value,
            user_id=self.current_user_id,
            price_per_liter=price
        )
        self.session.add(batch)
        self.session.commit()

        honey.quantity -= volume
        self.session.commit()

        self.accept()

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить клиента")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()

        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in ClientType])
        self.contact_input = QLineEdit()
        self.inn_input = QLineEdit()

        layout.addRow("Имя:", self.name_input)
        layout.addRow("Тип:", self.type_combo)
        layout.addRow("Контакт:", self.contact_input)
        layout.addRow("ИНН (опционально):", self.inn_input)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Добавить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.create_button.clicked.connect(self.create_client)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def create_client(self):
        name = self.name_input.text().strip()
        type_ = self.type_combo.currentText()
        contact = self.contact_input.text().strip()
        inn = self.inn_input.text().strip() or None
        if not name or not contact:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и контакт")
            return
        client = Client(name=name, type=type_, contact=contact, inn=inn)
        self.session.add(client)
        self.session.commit()
        self.accept()

class EditClientDialog(QDialog):
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать клиента")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.client = self.session.query(Client).filter_by(client_id=client_id).first()

        layout = QFormLayout()
        self.name_input = QLineEdit(self.client.name)
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in ClientType])
        self.type_combo.setCurrentText(self.client.type)
        self.contact_input = QLineEdit(self.client.contact)
        self.inn_input = QLineEdit(self.client.inn or "")

        layout.addRow("Имя:", self.name_input)
        layout.addRow("Тип:", self.type_combo)
        layout.addRow("Контакт:", self.contact_input)
        layout.addRow("ИНН (опционально):", self.inn_input)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.save_button.clicked.connect(self.save_client)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def save_client(self):
        name = self.name_input.text().strip()
        type_ = self.type_combo.currentText()
        contact = self.contact_input.text().strip()
        inn = self.inn_input.text().strip() or None
        if not name or not contact:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и контакт")
            return
        self.client.name = name
        self.client.type = type_
        self.client.contact = contact
        self.client.inn = inn
        self.session.commit()
        self.accept()

class AddOrderDialog(QDialog):
    def __init__(self, parent=None, current_user_id=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить заказ")
        self.setFixedSize(600,500)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.current_user_id = current_user_id

        layout = QVBoxLayout()
        self.client_combo = QComboBox()
        clients = self.session.query(Client).all()
        self.client_combo.addItems([c.name for c in clients])
        layout.addWidget(QLabel("Клиент:"))
        layout.addWidget(self.client_combo)

        self.items_table = QTableWidget(1, 3)
        self.items_table.setHorizontalHeaderLabels(["Продукция", "Объем (л)", "Стоимость (руб)"])
        self.product_combo = QComboBox()
        products = self.session.query(FinishedProduct).all()
        self.product_combo.addItems([f"Продукт {p.product_id} - {p.price_per_liter} руб/л" for p in products])
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(1, 1000)
        self.volume_spin.setValue(10)
        self.items_table.setCellWidget(0, 0, self.product_combo)
        self.items_table.setCellWidget(0, 1, self.volume_spin)
        self.items_table.setItem(0, 2, QTableWidgetItem("0 руб"))
        self.volume_spin.valueChanged.connect(self.update_cost)
        layout.addWidget(QLabel("Позиции:"))
        layout.addWidget(self.items_table)

        self.add_item_button = QPushButton("Добавить позицию")
        layout.addWidget(self.add_item_button)

        self.total_label = QLabel("Общая стоимость: 0 руб")
        layout.addWidget(self.total_label)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Дата:"))
        layout.addWidget(self.date_edit)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Создать")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.add_item_button.clicked.connect(self.add_item)
        self.create_button.clicked.connect(self.create_order)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def update_cost(self):
        for row in range(self.items_table.rowCount()):
            volume = self.items_table.cellWidget(row, 1).value()
            product_text = self.items_table.cellWidget(row, 0).currentText()
            price = float(product_text.split(" - ")[1].replace(" руб/л", ""))
            total_cost = volume * price
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{total_cost} руб"))
        self.update_total()

    def add_item(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        product_combo = QComboBox()
        products = self.session.query(FinishedProduct).all()
        product_combo.addItems([f"Продукт {p.product_id} - {p.price_per_liter} руб/л" for p in products])
        volume_spin = QDoubleSpinBox()
        volume_spin.setRange(1, 1000)
        volume_spin.setValue(10)
        volume_spin.valueChanged.connect(self.update_cost)
        self.items_table.setCellWidget(row, 0, product_combo)
        self.items_table.setCellWidget(row, 1, volume_spin)
        self.items_table.setItem(row, 2, QTableWidgetItem("0 руб"))

    def update_total(self):
        total = sum(float(self.items_table.item(row, 2).text().replace(" руб", "")) 
                    for row in range(self.items_table.rowCount()))
        self.total_label.setText(f"Общая стоимость: {total} руб")

    def create_order(self):
        client_name = self.client_combo.currentText()
        client = self.session.query(Client).filter_by(name=client_name).first()
        if not client:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return

        for row in range(self.items_table.rowCount()):
            product_text = self.items_table.cellWidget(row, 0).currentText()
            product_id = int(product_text.split(" - ")[0].replace("Продукт ", ""))
            volume = self.items_table.cellWidget(row, 1).value()
            product = self.session.query(FinishedProduct).filter_by(product_id=product_id).first()
            if product.available_volume < volume:
                QMessageBox.warning(self, "Ошибка", f"Недостаточно продукции {product_id} (нужно {volume} л, есть {product.available_volume} л)")
                return

        order = Order(
            client_id=client.client_id,
            order_date=self.date_edit.date().toString("yyyy-MM-dd"),
            status=OrderStatus.PENDING.value,
            user_id=self.current_user_id,
            total_order_cost=0
        )
        self.session.add(order)
        self.session.commit()

        for row in range(self.items_table.rowCount()):
            product_text = self.items_table.cellWidget(row, 0).currentText()
            product_id = int(product_text.split(" - ")[0].replace("Продукт ", ""))
            volume = self.items_table.cellWidget(row, 1).value()
            total_cost = float(self.items_table.item(row, 2).text().replace(" руб", ""))
            if volume <= 0 or total_cost < 0:
                QMessageBox.warning(self, "Ошибка", "Объем > 0, стоимость >= 0")
                return
            item = OrderItem(
                order_id=order.order_id,
                product_id=product_id,
                volume=volume,
                total_cost=total_cost
            )
            self.session.add(item)
            product = self.session.query(FinishedProduct).filter_by(product_id=product_id).first()
            product.available_volume -= volume
        self.session.commit()
        order.total_order_cost = sum(i.total_cost for i in order.order_items)
        self.session.commit()
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self, role="Технолог", user_id=None):
        super().__init__()
        self.role = UserRole(role)
        self.user_id = user_id
        self.session = Session()
        self.setWindowTitle("Учет медовых напитков")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        if self.role == UserRole.TECHNOLOGIST:
            self.init_raw_materials()
            self.init_production()
        elif self.role == UserRole.ASSISTANT:
            self.init_products()
            self.init_orders()
        elif self.role == UserRole.ENTREPRENEUR:
            self.init_raw_materials()
            self.init_production()
            self.init_products()
            self.init_orders()
            self.init_reports()
            self.init_charts()
        elif self.role == UserRole.ADMIN:
            self.init_users()

        self.notification_label = QLabel("Уведомления: проверка...")
        self.notification_label.setObjectName("notificationLabel")
        layout.addWidget(self.notification_label)
        self.update_notifications()

        self.setStyleSheet(APP_STYLE)

    def init_raw_materials(self):
        self.raw_tab = QWidget()
        self.tabs.addTab(self.raw_tab, "Сырье")
        raw_layout = QVBoxLayout(self.raw_tab)
        self.raw_search = QLineEdit()
        self.raw_search.setPlaceholderText("Поиск по названию...")
        self.raw_search.textChanged.connect(self.update_raw_table)
        raw_layout.addWidget(self.raw_search)
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(4)
        self.raw_table.setHorizontalHeaderLabels(["Название", "Кол-во", "Стоимость", "Дата закупки"])
        self.update_raw_table()
        raw_layout.addWidget(self.raw_table)
        button_layout = QHBoxLayout()
        self.add_raw_button = QPushButton("Добавить закупку")
        self.edit_raw_button = QPushButton("Редактировать")
        self.delete_raw_button = QPushButton("Удалить")
        button_layout.addWidget(self.add_raw_button)
        button_layout.addWidget(self.edit_raw_button)
        button_layout.addWidget(self.delete_raw_button)
        raw_layout.addLayout(button_layout)
        self.add_raw_button.clicked.connect(self.show_add_raw_material)
        self.edit_raw_button.clicked.connect(self.show_edit_raw_material)
        self.delete_raw_button.clicked.connect(self.delete_raw_material)

    def update_raw_table(self):
        search_text = self.raw_search.text().lower()
        materials = self.session.query(RawMaterial).filter(RawMaterial.name.ilike(f"%{search_text}%")).all()
        self.raw_table.setRowCount(len(materials))
        for i, m in enumerate(materials):
            self.raw_table.setItem(i, 0, QTableWidgetItem(m.name))
            self.raw_table.setItem(i, 1, QTableWidgetItem(f"{m.quantity} кг"))
            self.raw_table.setItem(i, 2, QTableWidgetItem(f"{m.cost} руб/кг"))
            self.raw_table.setItem(i, 3, QTableWidgetItem(str(m.purchase_date)))

    def show_edit_raw_material(self):
        selected_row = self.raw_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        name = self.raw_table.item(selected_row, 0).text()
        material = self.session.query(RawMaterial).filter_by(name=name).first()
        dialog = EditRawMaterialDialog(self, material.material_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_raw_table()
            self.update_notifications()

    def delete_raw_material(self):
        selected_row = self.raw_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        name = self.raw_table.item(selected_row, 0).text()
        material = self.session.query(RawMaterial).filter_by(name=name).first()
        if QMessageBox.question(self, "Подтверждение", f"Удалить {name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(material)
            self.session.commit()
            self.update_raw_table()
            self.update_notifications()

    def init_production(self):
        self.prod_tab = QTabWidget()
        self.tabs.addTab(self.prod_tab, "Производство")
        
        recipe_tab = QWidget()
        self.prod_tab.addTab(recipe_tab, "Рецепты")
        recipe_layout = QVBoxLayout(recipe_tab)
        self.recipe_search = QLineEdit()
        self.recipe_search.setPlaceholderText("Поиск по названию...")
        self.recipe_search.textChanged.connect(self.update_recipe_table)
        recipe_layout.addWidget(self.recipe_search)
        self.recipe_table = QTableWidget()
        self.recipe_table.setColumnCount(2)
        self.recipe_table.setHorizontalHeaderLabels(["Название", "Описание"])
        self.update_recipe_table()
        recipe_layout.addWidget(self.recipe_table)
        recipe_button_layout = QHBoxLayout()
        self.add_recipe_button = QPushButton("Добавить рецепт")
        self.edit_recipe_button = QPushButton("Редактировать")
        self.delete_recipe_button = QPushButton("Удалить")
        recipe_button_layout.addWidget(self.add_recipe_button)
        recipe_button_layout.addWidget(self.edit_recipe_button)
        recipe_button_layout.addWidget(self.delete_recipe_button)
        recipe_layout.addLayout(recipe_button_layout)
        self.add_recipe_button.clicked.connect(self.show_add_recipe)
        self.edit_recipe_button.clicked.connect(self.show_edit_recipe)
        self.delete_recipe_button.clicked.connect(self.delete_recipe)

        batch_tab = QWidget()
        self.prod_tab.addTab(batch_tab, "Партии")
        batch_layout = QVBoxLayout(batch_tab)
        self.batch_search = QLineEdit()
        self.batch_search.setPlaceholderText("Поиск по статусу...")
        self.batch_search.textChanged.connect(self.update_batch_table)
        batch_layout.addWidget(self.batch_search)
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels(["№", "Объем", "Статус", "Начало", "Готовность"])
        self.update_batch_table()
        batch_layout.addWidget(self.batch_table)
        batch_button_layout = QHBoxLayout()
        self.add_batch_button = QPushButton("Создать партию")
        batch_button_layout.addWidget(self.add_batch_button)
        batch_layout.addLayout(batch_button_layout)
        self.add_batch_button.clicked.connect(self.show_create_batch)

    def update_recipe_table(self):
        search_text = self.recipe_search.text().lower()
        recipes = self.session.query(Recipe).filter(Recipe.name.ilike(f"%{search_text}%")).all()
        self.recipe_table.setRowCount(len(recipes))
        for i, r in enumerate(recipes):
            self.recipe_table.setItem(i, 0, QTableWidgetItem(r.name))
            self.recipe_table.setItem(i, 1, QTableWidgetItem(r.description))

    def show_edit_recipe(self):
        selected_row = self.recipe_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        name = self.recipe_table.item(selected_row, 0).text()
        recipe = self.session.query(Recipe).filter_by(name=name).first()
        dialog = EditRecipeDialog(self, recipe.recipe_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_recipe_table()

    def delete_recipe(self):
        selected_row = self.recipe_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        name = self.recipe_table.item(selected_row, 0).text()
        recipe = self.session.query(Recipe).filter_by(name=name).first()
        if QMessageBox.question(self, "Подтверждение", f"Удалить {name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(recipe)
            self.session.commit()
            self.update_recipe_table()

    def update_batch_table(self):
        search_text = self.batch_search.text().lower()
        batches = self.session.query(Batch).filter(
            (Batch.status.ilike(f"%{search_text}%"))
        ).all()
        self.batch_table.setRowCount(len(batches))
        for i, b in enumerate(batches):
            self.batch_table.setItem(i, 0, QTableWidgetItem(str(b.batch_id)))
            self.batch_table.setItem(i, 1, QTableWidgetItem(f"{b.volume} л"))
            status_combo = QComboBox()
            status_combo.addItems([s.value for s in BatchStatus])
            status_combo.setCurrentText(b.status)
            status_combo.currentTextChanged.connect(lambda text, batch_id=b.batch_id: self.update_batch_status(batch_id, text))
            self.batch_table.setCellWidget(i, 2, status_combo)
            self.batch_table.setItem(i, 3, QTableWidgetItem(str(b.start_date)))
            self.batch_table.setItem(i, 4, QTableWidgetItem(str(b.end_date)))

    def update_batch_status(self, batch_id, status):
        batch = self.session.query(Batch).filter_by(batch_id=batch_id).first()
        if batch.status != status:
            batch.status = status
            if status == BatchStatus.READY.value:
                existing_product = self.session.query(FinishedProduct).filter_by(batch_id=batch.batch_id).first()
                if not existing_product:
                    finished_product = FinishedProduct(
                        batch_id=batch.batch_id,
                        volume=batch.volume,
                        available_volume=batch.volume,
                        production_date=str(batch.end_date),
                        price_per_liter=batch.price_per_liter
                    )
                    self.session.add(finished_product)
            self.session.commit()
            self.update_product_table()
        self.update_notifications()

    def init_products(self):
        self.product_tab = QWidget()
        self.tabs.addTab(self.product_tab, "Продукция")
        product_layout = QVBoxLayout(self.product_tab)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.dateChanged.connect(self.update_product_table)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.dateChanged.connect(self.update_product_table)

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Поиск по дате (гггг-мм-дд) или цене...")
        self.product_search.textChanged.connect(self.update_product_table)

        product_layout.addWidget(QLabel("Дата начала:"))
        product_layout.addWidget(self.start_date_edit)
        product_layout.addWidget(QLabel("Дата окончания:"))
        product_layout.addWidget(self.end_date_edit)
        product_layout.addWidget(self.product_search)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(["№", "Объем", "Доступно", "Дата розлива", "Цена/л"])
        self.update_product_table()
        product_layout.addWidget(self.product_table)

        product_button = QPushButton("Обновить")
        product_button.clicked.connect(self.update_product_table)
        product_layout.addWidget(product_button)

    def update_product_table(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        search_text = self.product_search.text().strip().lower()

        try:
            query = self.session.query(FinishedProduct).filter(
                FinishedProduct.production_date.between(start_date, end_date)
            )

            if search_text:
                try:
                    search_date = datetime.strptime(search_text, '%Y-%m-%d').date()
                    query = query.filter(FinishedProduct.production_date == search_date)
                except ValueError:
                    try:
                        search_price = float(search_text)
                        query = query.filter(FinishedProduct.price_per_liter == search_price)
                    except ValueError:
                        pass

            products = query.all()

            self.product_table.setRowCount(len(products))
            for i, p in enumerate(products):
                self.product_table.setItem(i, 0, QTableWidgetItem(str(p.product_id)))
                self.product_table.setItem(i, 1, QTableWidgetItem(f"{p.volume} л"))
                self.product_table.setItem(i, 2, QTableWidgetItem(f"{p.available_volume} л"))
                self.product_table.setItem(i, 3, QTableWidgetItem(str(p.production_date)))
                self.product_table.setItem(i, 4, QTableWidgetItem(f"{p.price_per_liter} руб"))

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при обновлении таблицы: {str(e)}")
            self.product_table.setRowCount(0)

    def init_orders(self):
        self.order_tab = QTabWidget()
        self.tabs.addTab(self.order_tab, "Клиенты и заказы")
        
        client_tab = QWidget()
        self.order_tab.addTab(client_tab, "Клиенты")
        client_layout = QVBoxLayout(client_tab)
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Поиск по имени...")
        self.client_search.textChanged.connect(self.update_client_table)
        client_layout.addWidget(self.client_search)
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(4)
        self.client_table.setHorizontalHeaderLabels(["Имя", "Тип", "Контакт", "ИНН"])
        self.update_client_table()
        client_layout.addWidget(self.client_table)
        client_button_layout = QHBoxLayout()
        self.add_client_button = QPushButton("Добавить клиента")
        self.edit_client_button = QPushButton("Редактировать")
        self.delete_client_button = QPushButton("Удалить")
        client_button_layout.addWidget(self.add_client_button)
        client_button_layout.addWidget(self.edit_client_button)
        client_button_layout.addWidget(self.delete_client_button)
        client_layout.addLayout(client_button_layout)
        self.add_client_button.clicked.connect(self.show_add_client)
        self.edit_client_button.clicked.connect(self.show_edit_client)
        self.delete_client_button.clicked.connect(self.delete_client)

        order_tab = QWidget()
        self.order_tab.addTab(order_tab, "Заказы")
        order_layout = QVBoxLayout(order_tab)
        self.order_search = QLineEdit()
        self.order_search.setPlaceholderText("Поиск по клиенту...")
        self.order_search.textChanged.connect(self.update_order_table)
        order_layout.addWidget(self.order_search)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(5)
        self.order_table.setHorizontalHeaderLabels(["№", "Клиент", "Дата", "Статус", "Стоимость"])
        self.update_order_table()
        order_layout.addWidget(self.order_table)
        order_button_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Добавить заказ")
        order_button_layout.addWidget(self.add_order_button)
        order_layout.addLayout(order_button_layout)
        self.add_order_button.clicked.connect(self.show_add_order)

    def update_client_table(self):
        search_text = self.client_search.text().lower()
        clients = self.session.query(Client).filter(Client.name.ilike(f"%{search_text}%")).all()
        self.client_table.setRowCount(len(clients))
        for i, c in enumerate(clients):
            self.client_table.setItem(i, 0, QTableWidgetItem(c.name))
            self.client_table.setItem(i, 1, QTableWidgetItem(c.type))
            self.client_table.setItem(i, 2, QTableWidgetItem(c.contact))
            self.client_table.setItem(i, 3, QTableWidgetItem(c.inn or "-"))

    def show_edit_client(self):
        selected_row = self.client_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        name = self.client_table.item(selected_row, 0).text()
        client = self.session.query(Client).filter_by(name=name).first()
        dialog = EditClientDialog(self, client.client_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_client_table()

    def delete_client(self):
        selected_row = self.client_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        name = self.client_table.item(selected_row, 0).text()
        client = self.session.query(Client).filter_by(name=name).first()
        if QMessageBox.question(self, "Подтверждение", f"Удалить {name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(client)
            self.session.commit()
            self.update_client_table()

    def update_order_table(self):
        search_text = self.order_search.text().lower()
        orders = self.session.query(Order).join(Client).filter(
            Client.name.ilike(f"%{search_text}%")
        ).all()
        self.order_table.setRowCount(len(orders))
        for i, o in enumerate(orders):
            self.order_table.setItem(i, 0, QTableWidgetItem(str(o.order_id)))
            self.order_table.setItem(i, 1, QTableWidgetItem(o.client.name))
            self.order_table.setItem(i, 2, QTableWidgetItem(str(o.order_date)))
            status_combo = QComboBox()
            status_combo.addItems([s.value for s in OrderStatus])
            status_combo.setCurrentText(o.status)
            status_combo.currentTextChanged.connect(lambda text, order_id=o.order_id: self.update_order_status(order_id, text))
            self.order_table.setCellWidget(i, 3, status_combo)
            self.order_table.setItem(i, 4, QTableWidgetItem(f"{o.total_order_cost} руб"))

    def update_order_status(self, order_id, status):
        order = self.session.query(Order).filter_by(order_id=order_id).first()
        order.status = status
        self.session.commit()
        self.update_notifications()

    def init_reports(self):
        self.report_tab = QWidget()
        self.tabs.addTab(self.report_tab, "Отчеты")
        report_layout = QVBoxLayout(self.report_tab)
        report_form = QFormLayout()
        self.report_type = QComboBox()
        self.report_type.addItems(["Остатки сырья", "Партии", "Заказы", "Доходы"])
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        report_form.addRow("Тип отчета:", self.report_type)
        report_form.addRow("Дата начала:", self.start_date)
        report_form.addRow("Дата окончания:", self.end_date)
        report_layout.addLayout(report_form)
        
        self.report_button = QPushButton("Сформировать PDF")
        report_layout.addWidget(self.report_button)
        
        self.report_button.clicked.connect(self.generate_report)

    def generate_report(self):
        report_type = self.report_type.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        font_path = "DejaVuSans.ttf"
        if not os.path.exists(font_path):
            QMessageBox.critical(self, "Ошибка", "Шрифт DejaVuSans.ttf не найден. Укажи правильный путь.")
            return
        
        default_filename = f"report_{report_type.lower().replace(' ', '_')}_{start_date}_to_{end_date}.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет как",
            default_filename,
            "PDF Files (*.pdf)"
        )
        if not output_file:
            return

        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        
        c = canvas.Canvas(output_file, pagesize=A4)
        c.setFont("DejaVuSans", 12)
        width, height = A4

        c.setFont("DejaVuSans", 16)
        c.drawCentredString(width / 2, height - 40, f"Отчет: {report_type}")
        c.setFont("DejaVuSans", 12)
        c.drawCentredString(width / 2, height - 60, f"Период: {start_date} - {end_date}")
        
        y = height - 100
        line_height = 20

        if report_type == "Остатки сырья":
            c.drawString(50, y, "Название   Кол-во   Стоимость   Дата закупки")
            y -= line_height
            c.line(50, y, width - 50, y)
            y -= 10
            materials = self.session.query(RawMaterial).filter(RawMaterial.purchase_date.between(start_date, end_date)).all()
            for m in materials:
                c.drawString(50, y, f"{m.name}")
                c.drawString(150, y, f"{m.quantity} кг")
                c.drawString(250, y, f"{m.cost} руб/кг")
                c.drawString(350, y, f"{m.purchase_date}")
                y -= line_height
                if y < 50:
                    c.showPage()
                    c.setFont("DejaVuSans", 12)
                    y = height - 50

        elif report_type == "Партии":
            c.drawString(50, y, "№   Объем   Статус   Начало   Готовность")
            y -= line_height
            c.line(50, y, width - 50, y)
            y -= 10
            batches = self.session.query(Batch).filter(Batch.start_date.between(start_date, end_date)).all()
            for b in batches:
                c.drawString(50, y, f"{b.batch_id}")
                c.drawString(100, y, f"{b.volume} л")
                c.drawString(200, y, f"{b.status}")
                c.drawString(300, y, f"{b.start_date}")
                c.drawString(400, y, f"{b.end_date}")
                y -= line_height
                if y < 50:
                    c.showPage()
                    c.setFont("DejaVuSans", 12)
                    y = height - 50

        elif report_type == "Заказы":
            c.drawString(50, y, "№   Клиент   Дата   Статус   Стоимость")
            y -= line_height
            c.line(50, y, width - 50, y)
            y -= 10
            orders = self.session.query(Order).filter(Order.order_date.between(start_date, end_date)).all()
            for o in orders:
                c.drawString(50, y, f"{o.order_id}")
                c.drawString(100, y, f"{o.client.name}")
                c.drawString(200, y, f"{o.order_date}")
                c.drawString(300, y, f"{o.status}")
                c.drawString(400, y, f"{o.total_order_cost} руб")
                y -= line_height
                if y < 50:
                    c.showPage()
                    c.setFont("DejaVuSans", 12)
                    y = height - 50

        elif report_type == "Доходы":
            c.drawString(50, y, "Дата   Доход")
            y -= line_height
            c.line(50, y, width - 50, y)
            y -= 10
            orders = self.session.query(Order).filter(
                Order.order_date.between(start_date, end_date),
                Order.status == OrderStatus.COMPLETED.value
            ).all()
            income_by_date = {}
            for o in orders:
                income_by_date[o.order_date] = income_by_date.get(o.order_date, 0) + o.total_order_cost
            for date, income in income_by_date.items():
                c.drawString(50, y, f"{date}")
                c.drawString(150, y, f"{income} руб")
                y -= line_height
                if y < 50:
                    c.showPage()
                    c.setFont("DejaVuSans", 12)
                    y = height - 50

        c.showPage()
        c.save()
        QMessageBox.information(self, "Успех", f"Отчет сохранен как {output_file}")

    def init_users(self):
        self.user_tab = QWidget()
        self.tabs.addTab(self.user_tab, "Пользователи")
        user_layout = QVBoxLayout(self.user_tab)
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("Поиск по логину...")
        self.user_search.textChanged.connect(self.update_user_table)
        user_layout.addWidget(self.user_search)
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["Логин", "Пароль", "Роль"])
        self.update_user_table()
        user_layout.addWidget(self.user_table)
        button_layout = QHBoxLayout()
        self.add_user_button = QPushButton("Добавить пользователя")
        self.edit_user_button = QPushButton("Редактировать пользователя")
        self.delete_user_button = QPushButton("Удалить")
        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.edit_user_button)
        button_layout.addWidget(self.delete_user_button)
        user_layout.addLayout(button_layout)
        self.add_user_button.clicked.connect(self.show_add_user)
        self.edit_user_button.clicked.connect(self.show_edit_user)
        self.delete_user_button.clicked.connect(self.delete_user)

    def update_user_table(self):
        search_text = self.user_search.text().lower()
        users = self.session.query(User).filter(User.login.ilike(f"%{search_text}%")).all()
        self.user_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.user_table.setItem(i, 0, QTableWidgetItem(u.login))
            self.user_table.setItem(i, 1, QTableWidgetItem("********"))
            self.user_table.setItem(i, 2, QTableWidgetItem(u.role))

    def delete_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления")
            return
        login = self.user_table.item(selected_row, 0).text()
        user = self.session.query(User).filter_by(login=login).first()
        if QMessageBox.question(self, "Подтверждение", f"Удалить {login}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(user)
            self.session.commit()
            self.update_user_table()

    def update_notifications(self):
        notifications = []
        today = QDate.currentDate().toString("yyyy-MM-dd")

        honey = self.session.query(RawMaterial).filter_by(name="Мед").first()
        if honey and honey.quantity < 10:
            notifications.append(f"Мед < 10 кг (осталось {honey.quantity} кг)")

        ready_batches = self.session.query(Batch).filter(
            Batch.status == BatchStatus.READY.value,
            Batch.end_date == today
        ).all()
        for batch in ready_batches:
            notifications.append(f"Партия №{batch.batch_id} готова")

        pending_orders = self.session.query(Order).filter(
            Order.status == OrderStatus.PENDING.value
        ).all()
        for order in pending_orders:
            notifications.append(f"Заказ №{order.order_id} ожидает выполнения")

        if notifications:
            self.notification_label.setText("Уведомления: " + "; ".join(notifications))
        else:
            self.notification_label.setText("Уведомления: нет активных")

    def show_add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_user_table()
            self.update_notifications()

    def show_edit_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return
        login = self.user_table.item(selected_row, 0).text()
        user = self.session.query(User).filter_by(login=login).first()
        dialog = EditUserDialog(self, user.user_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_user_table()
            self.update_notifications()

    def show_add_raw_material(self):
        dialog = AddRawMaterialDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_raw_table()
            self.update_notifications()

    def show_add_recipe(self):
        dialog = AddRecipeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_recipe_table()
            self.update_notifications()

    def show_create_batch(self):
        dialog = CreateBatchDialog(self, self.user_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_batch_table()
            self.update_product_table()
            self.update_notifications()

    def show_add_client(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_client_table()
            self.update_notifications()

    def show_add_order(self):
        dialog = AddOrderDialog(self, self.user_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_order_table()
            self.update_notifications()

    def init_charts(self):
        self.chart_tab = QWidget()
        self.tabs.addTab(self.chart_tab, "Графики")
        chart_layout = QVBoxLayout(self.chart_tab)

        self.chart_type = QComboBox()
        self.chart_type.addItems(["Доступный объем продукции", "Доходы по датам"])
        chart_layout.addWidget(QLabel("Тип графика:"))
        chart_layout.addWidget(self.chart_type)

        self.chart_button = QPushButton("Построить график")
        self.chart_button.clicked.connect(self.generate_chart)
        chart_layout.addWidget(self.chart_button)

        self.chart_label = QLabel()
        self.chart_label.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(self.chart_label)

    def generate_chart(self):
        chart_type = self.chart_type.currentText()
        if chart_type == "Доступный объем продукции":
            products = self.session.query(FinishedProduct).all()
            if not products:
                QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика")
                return
            product_ids = [str(p.product_id) for p in products]
            available_volumes = [p.available_volume for p in products]
            plt.figure(figsize=(10, 6))
            plt.bar(product_ids, available_volumes, color='skyblue')
            plt.title('Доступный объем продукции')
            plt.xlabel('ID продукта')
            plt.ylabel('Доступный объем (л)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path = "product_chart.png"
        elif chart_type == "Доходы по датам":
            orders = self.session.query(Order).filter(Order.status == OrderStatus.COMPLETED.value).all()
            if not orders:
                QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика")
                return
            income_by_date = {}
            for o in orders:
                income_by_date[o.order_date] = income_by_date.get(o.order_date, 0) + o.total_order_cost
            dates = list(income_by_date.keys())
            incomes = list(income_by_date.values())
            plt.figure(figsize=(10, 6))
            plt.plot(dates, incomes, marker='o', color='green')
            plt.title('Доходы по датам')
            plt.xlabel('Дата')
            plt.ylabel('Доход (руб)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path = "income_chart.png"

        plt.savefig(chart_path)
        plt.close()

        pixmap = QPixmap(chart_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить график")
            return
        self.chart_label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))