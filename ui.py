import bcrypt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, 
                               QComboBox, QDialog, QLabel, QFormLayout, QDoubleSpinBox, QDateEdit,
                               QMessageBox, QFileDialog, QHeaderView)
from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from sqlalchemy import func
from models import Session, User, RawMaterial, Recipe, Batch, FinishedProduct, Client, Order, OrderItem, UserRole, BatchStatus, ClientType, OrderStatus, PriceChange
from datetime import datetime
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def log_price_change(session, table_name, record_id, old_price, new_price, login):
    price_change = PriceChange(
        table_name=table_name,
        record_id=record_id,
        old_price=old_price,
        new_price=new_price,
        login=login
    )
    session.add(price_change)
    session.commit()

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

class MainWindow(QMainWindow):
    def __init__(self, role="Технолог", user_id=None):
        super().__init__()
        self.role = UserRole(role)
        self.user_id = user_id
        self.session = Session()
        self.setWindowTitle("Учет медовых напитков")
        self.setWindowIcon(QIcon("icon.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.notification_label = QLabel("Уведомления: проверка...")
        self.notification_label.setObjectName("notificationLabel")
        layout.addWidget(self.notification_label)

        central_widget.setLayout(layout)
        self.showMaximized()
        self.setStyleSheet(APP_STYLE)

        QTimer.singleShot(0, self.initialize_content)

    def initialize_content(self):
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

        self.update_notifications()

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
        self.raw_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.raw_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
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
        try:
            search_text = self.raw_search.text().lower()
            materials = self.session.query(RawMaterial).filter(RawMaterial.name.ilike(f"%{search_text}%")).all()
            self.raw_table.setRowCount(len(materials))
            for i, m in enumerate(materials):
                self.raw_table.setItem(i, 0, QTableWidgetItem(m.name))
                self.raw_table.setItem(i, 1, QTableWidgetItem(f"{m.quantity} {m.unit}"))
                self.raw_table.setItem(i, 2, QTableWidgetItem(f"{m.cost} руб/{m.unit}"))
                self.raw_table.setItem(i, 3, QTableWidgetItem(str(m.purchase_date)))
            self.raw_table.resizeColumnsToContents()
            self.raw_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.raw_table.setRowCount(0)

    def show_edit_raw_material(self):
        selected_row = self.raw_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        name = self.raw_table.item(selected_row, 0).text()
        material = self.session.query(RawMaterial).filter_by(name=name).first()
        dialog = EditRawMaterialDialog(self, material.material_id, self.user_id)
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
        self.recipe_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recipe_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
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
        self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.batch_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.update_batch_table()
        batch_layout.addWidget(self.batch_table)
        batch_button_layout = QHBoxLayout()
        self.add_batch_button = QPushButton("Создать партию")
        self.edit_batch_button = QPushButton("Редактировать")
        self.delete_batch_button = QPushButton("Удалить")
        batch_button_layout.addWidget(self.add_batch_button)
        batch_button_layout.addWidget(self.edit_batch_button)
        batch_button_layout.addWidget(self.delete_batch_button)
        batch_layout.addLayout(batch_button_layout)
        self.add_batch_button.clicked.connect(self.show_create_batch)
        self.edit_batch_button.clicked.connect(self.show_edit_batch)
        self.delete_batch_button.clicked.connect(self.delete_batch)

    def update_recipe_table(self):
        try:
            search_text = self.recipe_search.text().lower()
            recipes = self.session.query(Recipe).filter(Recipe.name.ilike(f"%{search_text}%")).all()
            self.recipe_table.setRowCount(len(recipes))
            for i, r in enumerate(recipes):
                self.recipe_table.setItem(i, 0, QTableWidgetItem(r.name))
                self.recipe_table.setItem(i, 1, QTableWidgetItem(r.description))
            self.recipe_table.resizeColumnsToContents()
            self.recipe_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.recipe_table.setRowCount(0)

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
        used_in_batches = self.session.query(Batch).filter_by(recipe_id=recipe.recipe_id).first()
        if used_in_batches:
            QMessageBox.warning(self, "Ошибка", "Рецепт используется в партиях и не может быть удален")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить {name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(recipe)
            self.session.commit()
            self.update_recipe_table()
            self.update_notifications()

    def update_batch_table(self):
        try:
            search_text = self.batch_search.text().lower()
            batches = self.session.query(Batch).filter(Batch.status.ilike(f"%{search_text}%")).all()
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
                self.batch_table.setItem(i, 4, QTableWidgetItem(str(b.end_date or 'Не завершено')))
            self.batch_table.resizeColumnsToContents()
            self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.batch_table.setRowCount(0)

    def update_batch_status(self, batch_id, status):
        try:
            batch = self.session.query(Batch).filter_by(batch_id=batch_id).first()
            if batch.status != status:
                batch.status = status
                if status == BatchStatus.READY.value:
                    existing_product = self.session.query(FinishedProduct).filter_by(batch_id=batch.batch_id).first()
                    if not existing_product:
                        recipe_name = self.session.query(Recipe).filter_by(recipe_id=batch.recipe_id).first().name
                        finished_product = FinishedProduct(
                            batch_id=batch.batch_id,
                            volume=batch.volume,
                            available_volume=batch.volume,
                            production_date=str(batch.end_date),
                            price_per_liter=batch.price_per_liter,
                            recipe_name=recipe_name
                        )
                        self.session.add(finished_product)
                self.session.commit()
                self.update_product_table()
            self.update_notifications()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статус: {str(e)}")

    def show_edit_batch(self):
        selected_row = self.batch_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        batch_id = int(self.batch_table.item(selected_row, 0).text())
        batch = self.session.query(Batch).filter_by(batch_id=batch_id).first()
        dialog = EditBatchDialog(self, batch.batch_id, self.user_id)
        if dialog.exec() == QDialog.Accepted:
            self.update_batch_table()
            self.update_product_table()
            self.update_notifications()

    def delete_batch(self):
        selected_row = self.batch_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        batch_id = int(self.batch_table.item(selected_row, 0).text())
        batch = self.session.query(Batch).filter_by(batch_id=batch_id).first()
        if QMessageBox.question(self, "Подтверждение", f"Удалить партию №{batch_id}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(batch)
            self.session.commit()
            self.update_batch_table()
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
        self.product_table.setHorizontalHeaderLabels(["Название", "Объем", "Доступно", "Дата розлива", "Цена/л"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.update_product_table()
        product_layout.addWidget(self.product_table)

        product_button = QPushButton("Обновить")
        product_button.clicked.connect(self.update_product_table)
        product_layout.addWidget(product_button)

    def update_product_table(self):
        try:
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            search_text = self.product_search.text().strip().lower()

            query = self.session.query(FinishedProduct).join(Batch).join(Recipe).filter(
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
                recipe_name = self.session.query(Recipe).filter_by(recipe_id=p.batch.recipe_id).first().name
                self.product_table.setItem(i, 0, QTableWidgetItem(recipe_name))
                self.product_table.setItem(i, 1, QTableWidgetItem(f"{p.volume} л"))
                self.product_table.setItem(i, 2, QTableWidgetItem(f"{p.available_volume} л"))
                self.product_table.setItem(i, 3, QTableWidgetItem(str(p.production_date)))
                self.product_table.setItem(i, 4, QTableWidgetItem(f"{p.price_per_liter} руб"))
            self.product_table.resizeColumnsToContents()
            self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
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
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.update_order_table()
        order_layout.addWidget(self.order_table)
        order_button_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Добавить заказ")
        self.delete_order_button = QPushButton("Удалить")
        order_button_layout.addWidget(self.add_order_button)
        order_button_layout.addWidget(self.delete_order_button)
        order_layout.addLayout(order_button_layout)
        self.add_order_button.clicked.connect(self.show_add_order)
        self.delete_order_button.clicked.connect(self.delete_order)

    def update_client_table(self):
        try:
            search_text = self.client_search.text().lower()
            clients = self.session.query(Client).filter(Client.name.ilike(f"%{search_text}%")).all()
            self.client_table.setRowCount(len(clients))
            for i, c in enumerate(clients):
                self.client_table.setItem(i, 0, QTableWidgetItem(c.name))
                self.client_table.setItem(i, 1, QTableWidgetItem(c.type))
                self.client_table.setItem(i, 2, QTableWidgetItem(c.contact))
                self.client_table.setItem(i, 3, QTableWidgetItem(c.inn or "-"))
            self.client_table.resizeColumnsToContents()
            self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.client_table.setRowCount(0)

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
        orders_exist = self.session.query(Order).filter_by(client_id=client.client_id).first()
        if orders_exist:
            QMessageBox.warning(self, "Ошибка", "Клиент имеет связанные заказы и не может быть удален")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить {name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(client)
            self.session.commit()
            self.update_client_table()
            self.update_notifications()

    def update_order_table(self):
        try:
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
            self.order_table.resizeColumnsToContents()
            self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.order_table.setRowCount(0)

    def update_order_status(self, order_id, status):
        try:
            order = self.session.query(Order).filter_by(order_id=order_id).first()
            order.status = status
            self.session.commit()
            self.update_notifications()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статус: {str(e)}")

    def delete_order(self):
        selected_row = self.order_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        order_id = int(self.order_table.item(selected_row, 0).text())
        order = self.session.query(Order).filter_by(order_id=order_id).first()
        order_items = self.session.query(OrderItem).filter_by(order_id=order_id).all()
        if QMessageBox.question(self, "Подтверждение", f"Удалить заказ №{order_id}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for item in order_items:
                product = self.session.query(FinishedProduct).filter_by(product_id=item.product_id).first()
                if product:
                    product.available_volume += item.volume
            self.session.commit()
            self.session.query(OrderItem).filter_by(order_id=order_id).delete()
            self.session.delete(order)
            self.session.commit()
            self.update_order_table()
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
            QMessageBox.critical(self, "Ошибка", "Шрифт DejaVuSans.ttf не найден. Укажите правильный путь.")
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

        try:
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
            col_widths = [120, 80, 60, 80, 140]
            col_widths_income = [100, 100]

            if report_type == "Остатки сырья":
                headers = ["Название", "Кол-во", "Ед.изм", "Стоимость", "Дата закупки"]
                x_positions = [50, 190, 270, 330, 410]
                for i, header in enumerate(headers):
                    c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                y -= line_height
                c.line(50, y, width - 50, y)
                y -= 10
                materials = self.session.query(RawMaterial).filter(RawMaterial.purchase_date.between(start_date, end_date)).all()
                if not materials:
                    c.drawString(50, y, "Данные за выбранный период отсутствуют")
                else:
                    for m in materials:
                        c.drawString(x_positions[0] + 27, y, f"{m.name[:15]:<15}")
                        c.drawCentredString(x_positions[1] + col_widths[1] / 2, y, f"{m.quantity:>6.2f}")
                        c.drawCentredString(x_positions[2] + col_widths[2] / 2, y, f"{m.unit}")
                        c.drawRightString(x_positions[3] + col_widths[3], y, f"{m.cost:>6.2f} руб")
                        c.drawString(x_positions[4] + 30, y, f"{m.purchase_date}")
                        y -= line_height
                        if y < 100:
                            c.showPage()
                            y = height - 50
                            for i, header in enumerate(headers):
                                c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                            y -= line_height
                            c.line(50, y, width - 50, y)
                            y -= 10

            elif report_type == "Партии":
                headers = ["№", "Объем", "Статус", "Начало", "Готовность"]
                x_positions = [50, 150, 230, 290, 370]
                for i, header in enumerate(headers):
                    c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                y -= line_height
                c.line(50, y, width - 50, y)
                y -= 10
                batches = self.session.query(Batch).filter(Batch.start_date.between(start_date, end_date)).all()
                if not batches:
                    c.drawString(50, y, "Данные за выбранный период отсутствуют")
                else:
                    for b in batches:
                        c.drawCentredString(x_positions[0] + col_widths[0] / 2, y, str(b.batch_id))
                        c.drawRightString(x_positions[1] + col_widths[1], y, f"{b.volume:>6.2f} л")
                        c.drawCentredString(x_positions[2] + col_widths[2] / 2, y, f"{b.status}")
                        c.drawString(x_positions[3], y, f"{b.start_date}")
                        c.drawString(x_positions[4], y, f"{b.end_date or 'Не завершено'}")
                        y -= line_height
                        if y < 100:
                            c.showPage()
                            y = height - 50
                            for i, header in enumerate(headers):
                                c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                            y -= line_height
                            c.line(50, y, width - 50, y)
                            y -= 10

            elif report_type == "Заказы":
                headers = ["№", "Клиент", "Дата", "Статус", "Стоимость"]
                x_positions = [50, 150, 230, 290, 370]
                for i, header in enumerate(headers):
                    c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                y -= line_height
                c.line(50, y, width - 50, y)
                y -= 10
                orders = self.session.query(Order).filter(Order.order_date.between(start_date, end_date)).all()
                if not orders:
                    c.drawString(50, y, "Данные за выбранный период отсутствуют")
                else:
                    for o in orders:
                        client = self.session.query(Client).filter_by(client_id=o.client_id).first()
                        client_name = client.name if client else "Неизвестно"
                        c.drawCentredString(x_positions[0] + col_widths[0] / 2, y, str(o.order_id))
                        c.drawRightString(x_positions[1] + col_widths[1], y, f"{client_name[:15]:<15}")
                        c.drawString(x_positions[2], y, f"{o.order_date}")
                        c.drawCentredString(x_positions[3] + col_widths[3] / 2, y, f"{o.status}")
                        c.drawRightString(x_positions[4] + col_widths[4], y, f"{o.total_order_cost:>8.2f} руб")
                        y -= line_height
                        if y < 100:
                            c.showPage()
                            y = height - 50
                            for i, header in enumerate(headers):
                                c.drawCentredString(x_positions[i] + col_widths[i] / 2, y, header)
                            y -= line_height
                            c.line(50, y, width - 50, y)
                            y -= 10

            elif report_type == "Доходы":
                headers = ["Дата", "Доход"]
                x_positions = [50, 150]
                for i, header in enumerate(headers):
                    c.drawCentredString(x_positions[i] + col_widths_income[i] / 2, y, header)
                y -= line_height
                c.line(50, y, width - 50, y)
                y -= 10
                orders = self.session.query(Order).filter(
                    Order.order_date.between(start_date, end_date),
                    Order.status == OrderStatus.COMPLETED.value
                ).all()
                if not orders:
                    c.drawString(50, y, "Данные за выбранный период отсутствуют")
                else:
                    income_by_date = {}
                    for o in orders:
                        income_by_date[o.order_date] = income_by_date.get(o.order_date, 0) + o.total_order_cost
                    for date, income in income_by_date.items():
                        c.drawString(x_positions[0], y, f"{date}")
                        c.drawRightString(x_positions[1] + col_widths_income[1], y, f"{income:>8.2f} руб")
                        y -= line_height
                        if y < 100:
                            c.showPage()
                            y = height - 50
                            for i, header in enumerate(headers):
                                c.drawCentredString(x_positions[i] + col_widths_income[i] / 2, y, header)
                            y -= line_height
                            c.line(50, y, width - 50, y)
                            y -= 10

            y = 70
            c.drawString(50, y, "Руководитель: ____________/____________________")
            y -= 20
            c.drawString(50, y, "                           (подпись)       (расшифровка)")

            c.showPage()
            c.save()
            QMessageBox.information(self, "Успех", f"Отчет сохранен как {output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать отчет: {str(e)}")
        finally:
            self.session.close()

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
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
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
        try:
            search_text = self.user_search.text().lower()
            users = self.session.query(User).filter(User.login.ilike(f"%{search_text}%")).all()
            self.user_table.setRowCount(len(users))
            for i, u in enumerate(users):
                self.user_table.setItem(i, 0, QTableWidgetItem(u.login))
                self.user_table.setItem(i, 1, QTableWidgetItem("********"))
                self.user_table.setItem(i, 2, QTableWidgetItem(u.role))
            self.user_table.resizeColumnsToContents()
            self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            self.user_table.setRowCount(0)

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
        try:
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
        except Exception as e:
            self.notification_label.setText(f"Уведомления: ошибка подключения - {str(e)}")

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
        try:
            chart_type = self.chart_type.currentText()
            plt.figure(figsize=(10, 6))
            if chart_type == "Доступный объем продукции":
                products = self.session.query(FinishedProduct).all()
                if not products:
                    QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика")
                    return
                product_names = [self.session.query(Recipe).filter_by(recipe_id=p.batch.recipe_id).first().name for p in products]
                available_volumes = [p.available_volume for p in products]
                plt.bar(product_names, available_volumes, color='skyblue')
                plt.title('Доступный объем продукции')
                plt.xlabel('Название медовухи')
                plt.ylabel('Доступный объем (л)')
                plt.xticks(rotation=45)
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
                plt.plot(dates, incomes, marker='o', color='green')
                plt.title('Доходы по датам')
                plt.xlabel('Дата')
                plt.ylabel('Доход (руб)')
                plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path = f"{chart_type.lower().replace(' ', '_')}_chart.png"
            plt.savefig(chart_path)
            plt.close()
            self.chart_label.setPixmap(QPixmap(chart_path))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось построить график: {str(e)}")

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
        self.setFixedSize(350, 300)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()

        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 10000)
        self.quantity_spin.setValue(10)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["кг", "л", "шт"])
        self.unit_combo.setCurrentText("кг")
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10000)
        self.cost_spin.setValue(100)
        self.cost_spin.setSuffix(" руб/ед")
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())

        layout.addRow("Название:", self.name_input)
        layout.addRow("Количество:", self.quantity_spin)
        layout.addRow("Единица измерения:", self.unit_combo)
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

    def create_raw_material(self):
        name = self.name_input.text().strip()
        quantity = self.quantity_spin.value()
        unit = self.unit_combo.currentText()
        cost = self.cost_spin.value()
        purchase_date = self.purchase_date.date().toString("yyyy-MM-dd")

        if not name or quantity <= 0 or cost <= 0:
            QMessageBox.warning(self, "Ошибка", "Заполните название, количество и стоимость корректно")
            return

        try:
            material = RawMaterial(
                name=name,
                quantity=quantity,
                unit=unit,
                cost=cost,
                purchase_date=purchase_date,
                min_quantity=0
            )
            self.session.add(material)
            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить закупку: {str(e)}")
        finally:
            self.session.close()

class EditRawMaterialDialog(QDialog):
    def __init__(self, parent=None, material_id=None, user_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать закупку")
        self.setFixedSize(350, 300)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.material = self.session.query(RawMaterial).filter_by(material_id=material_id).first()
        self.user_id = user_id

        layout = QFormLayout()
        self.name_input = QLineEdit(self.material.name)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 10000)
        self.quantity_spin.setValue(self.material.quantity)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["кг", "л", "шт"])
        self.unit_combo.setCurrentText(self.material.unit if self.material.unit else "кг")
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10000)
        self.cost_spin.setValue(self.material.cost)
        self.cost_spin.setSuffix(" руб/ед")
        self.purchase_date = QDateEdit()
        purchase_date_str = str(self.material.purchase_date)
        self.purchase_date.setDate(QDate.fromString(purchase_date_str, "yyyy-MM-dd"))

        layout.addRow("Название:", self.name_input)
        layout.addRow("Количество:", self.quantity_spin)
        layout.addRow("Единица измерения:", self.unit_combo)
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

    def save_material(self):
        name = self.name_input.text().strip()
        quantity = self.quantity_spin.value()
        unit = self.unit_combo.currentText()
        new_cost = self.cost_spin.value()
        purchase_date = self.purchase_date.date().toString("yyyy-MM-dd")

        if not name or quantity <= 0 or new_cost <= 0:
            QMessageBox.warning(self, "Ошибка", "Заполните название, количество и стоимость корректно")
            return

        try:
            old_cost = self.material.cost
            if old_cost != new_cost:
                login = self.session.query(User).filter_by(user_id=self.user_id).first().login if self.user_id else "unknown"
                log_price_change(self.session, "raw_materials", self.material.material_id, old_cost, new_cost, login)

            self.material.name = name
            self.material.quantity = quantity
            self.material.unit = unit
            self.material.cost = new_cost
            self.material.purchase_date = purchase_date
            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")
        finally:
            self.session.close()

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

class EditBatchDialog(QDialog):
    def __init__(self, parent=None, batch_id=None, user_id=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать партию")
        self.setFixedSize(350, 250)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.batch = self.session.query(Batch).filter_by(batch_id=batch_id).first()
        self.user_id = user_id

        layout = QFormLayout()
        self.recipe_combo = QComboBox()
        recipes = self.session.query(Recipe).all()
        self.recipe_combo.addItems([r.name for r in recipes])
        self.recipe_combo.setCurrentText(self.batch.recipe.name)
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(1, 1000)
        self.volume_spin.setValue(self.batch.volume)
        self.volume_spin.setSuffix(" л")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.fromString(self.batch.start_date, "yyyy-MM-dd"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 10000)
        self.price_spin.setValue(self.batch.price_per_liter)
        self.price_spin.setSuffix(" руб/л")

        layout.addRow("Рецепт:", self.recipe_combo)
        layout.addRow("Объем:", self.volume_spin)
        layout.addRow("Дата начала:", self.start_date)
        layout.addRow("Цена за литр:", self.price_spin)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.save_button.clicked.connect(self.save_batch)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)
        self.setStyleSheet(APP_STYLE)

    def save_batch(self):
        recipe_name = self.recipe_combo.currentText()
        recipe = self.session.query(Recipe).filter_by(name=recipe_name).first()
        volume = self.volume_spin.value()
        new_price = self.price_spin.value()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        if not recipe or volume <= 0 or new_price < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите рецепт, объем > 0, цена >= 0")
            return

        try:
            old_price = self.batch.price_per_liter
            if old_price != new_price:
                login = self.session.query(User).filter_by(user_id=self.user_id).first().login if self.user_id else "unknown"
                log_price_change(self.session, "batches", self.batch.batch_id, old_price, new_price, login)

            self.batch.recipe_id = recipe.recipe_id
            self.batch.volume = volume
            self.batch.start_date = start_date
            self.batch.end_date = self.start_date.date().addDays(14).toString("yyyy-MM-dd")
            self.batch.price_per_liter = new_price
            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")
        finally:
            self.session.close()

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
        self.setFixedSize(600, 500)
        self.setWindowIcon(QIcon("icon.png"))
        self.session = Session()
        self.current_user_id = current_user_id

        layout = QVBoxLayout()
        self.client_combo = QComboBox()
        clients = self.session.query(Client).all()
        self.client_combo.addItems([c.name for c in clients])
        layout.addWidget(QLabel("Клиент:"))
        layout.addWidget(self.client_combo)

        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["Медовуха", "Объем (л)", "Стоимость (руб)"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        layout.addWidget(QLabel("Позиции:"))
        layout.addWidget(self.items_table)

        self.add_item_button = QPushButton("Добавить позицию")
        self.add_item_button.clicked.connect(self.add_item)
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

        self.create_button.clicked.connect(self.create_order)
        self.cancel_button.clicked.connect(self.reject)
        self.setLayout(layout)

    def add_item(self):
        row_position = self.items_table.rowCount()
        self.items_table.insertRow(row_position)
        
        product_combo = QComboBox()
        if not hasattr(self, 'products'):
            finished_products = self.session.query(FinishedProduct).join(Batch).join(Recipe).all()
            self.products = [
                (fp.product_id, self.session.query(Recipe).filter_by(recipe_id=fp.batch.recipe_id).first().name, fp.available_volume, fp.price_per_liter)
                for fp in finished_products
            ]
        product_combo.addItems([p[1] for p in self.products])
        product_combo.currentIndexChanged.connect(lambda: self.update_cost(row_position))
        self.items_table.setCellWidget(row_position, 0, product_combo)
        
        volume_input = QDoubleSpinBox()
        volume_input.setRange(1, 1000)
        volume_input.setValue(10)
        volume_input.valueChanged.connect(lambda: self.update_cost(row_position))
        self.items_table.setCellWidget(row_position, 1, volume_input)
        
        cost_item = QTableWidgetItem("0 руб")
        self.items_table.setItem(row_position, 2, cost_item)
        
        self.update_cost(row_position)

    def update_cost(self, row):
        volume = self.items_table.cellWidget(row, 1).value()
        product_combo = self.items_table.cellWidget(row, 0)
        product_index = product_combo.currentIndex()
        if product_index >= 0 and product_index < len(self.products):
            _, _, available_volume, price_per_liter = self.products[product_index]
            if volume > available_volume:
                QMessageBox.warning(self, "Ошибка", f"Доступный объем: {available_volume} л")
                volume_input = self.items_table.cellWidget(row, 1)
                volume_input.setValue(min(volume, available_volume))
                return
            cost = volume * price_per_liter
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{cost:.2f} руб"))
            self.update_total()

    def update_total(self):
        total = 0
        for row in range(self.items_table.rowCount()):
            cost_item = self.items_table.item(row, 2)
            if cost_item and cost_item.text().replace(" руб", "").strip():
                total += float(cost_item.text().replace(" руб", ""))
        self.total_label.setText(f"Общая стоимость: {total:.2f} руб")

    def create_order(self):
        client_name = self.client_combo.currentText()
        client = self.session.query(Client).filter_by(name=client_name).first()
        order_date = self.date_edit.date().toString("yyyy-MM-dd")
        total_cost = float(self.total_label.text().replace("Общая стоимость: ", "").replace(" руб", ""))

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну позицию")
            return

        order = Order(
            client_id=client.client_id,
            order_date=order_date,
            total_order_cost=total_cost,
            status=OrderStatus.PENDING.value,
            user_id=self.current_user_id
        )
        self.session.add(order)
        self.session.commit()

        for row in range(self.items_table.rowCount()):
            product_combo = self.items_table.cellWidget(row, 0)
            volume_input = self.items_table.cellWidget(row, 1)
            product_index = product_combo.currentIndex()
            if product_index >= 0 and product_index < len(self.products):
                product_id, _, _, _ = self.products[product_index]
                volume = volume_input.value()
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product_id,
                    volume=volume
                )
                self.session.add(order_item)
                product = self.session.query(FinishedProduct).filter_by(product_id=product_id).first()
                if product:
                    product.available_volume -= volume
                    self.session.commit()
        self.session.commit()
        self.accept()