import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QLineEdit, QComboBox, QDoubleSpinBox, QTableWidgetItem
from PySide6.QtCore import QDate
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ui import LoginWindow, CreateBatchDialog, AddOrderDialog, MainWindow, EditRawMaterialDialog
from models import Base, User, RawMaterial, Recipe, Batch, Client, FinishedProduct, Order, OrderItem
import bcrypt

# Фикстура для создания QApplication
@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

# Фикстура для создания базы данных
@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()

# Фикстура для очистки базы перед каждым тестом
@pytest.fixture
def clean_db(db_session):
    db_session.query(User).delete()
    db_session.query(RawMaterial).delete()
    db_session.query(Recipe).delete()
    db_session.query(Batch).delete()
    db_session.query(Client).delete()
    db_session.query(FinishedProduct).delete()
    db_session.query(Order).delete()
    db_session.query(OrderItem).delete()
    db_session.commit()
    return db_session

def test_login_success(clean_db, app):
    """Тест успешной авторизации с реальными QLineEdit"""
    session = clean_db
    # Хешируем пароль с помощью bcrypt
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(login="admin", password=hashed_password, role="Администратор")
    session.add(user)
    session.commit()

    dialog = LoginWindow()
    dialog.session = session
    dialog.login_input = QLineEdit()
    dialog.login_input.setText("admin")
    dialog.password_input = QLineEdit()
    dialog.password_input.setText("admin123")

    with patch.object(dialog, 'accept') as mock_accept:
        dialog.validate_and_accept()
        mock_accept.assert_called_once()
        assert dialog.user_id == user.user_id  # Теперь user_id должен быть

def test_login_invalid_password(clean_db):
    """Тест авторизации с неправильным паролем"""
    session = clean_db
    # Хешируем пароль с помощью bcrypt
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(login="admin", password=hashed_password, role="Администратор")
    session.add(user)
    session.commit()

    dialog = LoginWindow()
    dialog.session = session
    dialog.login_input = MagicMock()
    dialog.login_input.text.return_value = "admin"
    dialog.password_input = MagicMock()
    dialog.password_input.text.return_value = "wrongpassword"

    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
        dialog.validate_and_accept()
        mock_warning.assert_called_once()
        assert "Неверный логин или пароль" in mock_warning.call_args[0][2]

def test_create_batch_success(clean_db):
    """Тест создания партии с достаточным количеством сырья"""
    session = clean_db
    honey = RawMaterial(name="Мед", quantity=250.0, cost=300.0, purchase_date="2025-01-15")
    recipe = Recipe(name="Медовуха классическая", description="Мед, вода, дрожжи")
    session.add(honey)
    session.add(recipe)
    session.commit()

    dialog = CreateBatchDialog(current_user_id=1)
    dialog.session = session
    dialog.recipe_combo = MagicMock()
    dialog.recipe_combo.currentText.return_value = "Медовуха классическая"
    dialog.volume_spin = MagicMock()
    dialog.volume_spin.value.return_value = 100.0
    dialog.start_date = MagicMock()
    dialog.start_date.date.return_value = QDate(2025, 4, 10)
    dialog.price_spin = MagicMock()
    dialog.price_spin.value.return_value = 600.0

    with patch.object(dialog, 'accept') as mock_accept:
        dialog.create_batch()
        mock_accept.assert_called_once()

    batch = session.query(Batch).first()
    assert batch is not None
    assert batch.volume == 100.0
    assert batch.status == "В брожении"
    assert batch.price_per_liter == 600.0
    updated_honey = session.query(RawMaterial).filter_by(name="Мед").first()
    assert updated_honey.quantity == 150.0  # Списано 100 кг

def test_create_batch_insufficient_honey(clean_db):
    """Тест создания партии с недостаточным количеством меда"""
    session = clean_db
    honey = RawMaterial(name="Мед", quantity=50.0, cost=300.0, purchase_date="2025-01-15")
    recipe = Recipe(name="Медовуха классическая", description="Мед, вода, дрожжи")
    session.add(honey)
    session.add(recipe)
    session.commit()

    dialog = CreateBatchDialog(current_user_id=1)
    dialog.session = session
    dialog.recipe_combo = MagicMock()
    dialog.recipe_combo.currentText.return_value = "Медовуха классическая"
    dialog.volume_spin = MagicMock()
    dialog.volume_spin.value.return_value = 100.0
    dialog.start_date = MagicMock()
    dialog.start_date.date.return_value = QDate(2025, 4, 10)
    dialog.price_spin = MagicMock()
    dialog.price_spin.value.return_value = 600.0

    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
        dialog.create_batch()
        mock_warning.assert_called_once()
        assert "Недостаточно меда" in mock_warning.call_args[0][2]

    batch = session.query(Batch).first()
    assert batch is None

def test_create_order_success(clean_db):
    """Тест создания заказа с несколькими позициями"""
    session = clean_db
    client = Client(name="ООО Медовый край", type="Юрлицо", contact="info@medkray.ru", inn="123456789012")
    product1 = FinishedProduct(product_id=1, batch_id=1, volume=200.0, available_volume=150.0, production_date="2025-02-15", price_per_liter=600.0)
    product3 = FinishedProduct(product_id=3, batch_id=3, volume=100.0, available_volume=80.0, production_date="2025-03-02", price_per_liter=700.0)
    session.add(client)
    session.add(product1)
    session.add(product3)
    session.commit()

    dialog = AddOrderDialog(current_user_id=1)
    dialog.session = session
    dialog.client_combo = MagicMock()
    dialog.client_combo.currentText.return_value = "ООО Медовый край"
    dialog.date_edit = MagicMock()
    dialog.date_edit.date.return_value = QDate(2025, 4, 10)
    dialog.items_table = MagicMock()
    dialog.items_table.rowCount.return_value = 2
    combo1 = MagicMock()
    combo1.currentText.return_value = "Продукт 1 - Медовуха классическая"
    volume_spin1 = QDoubleSpinBox()
    volume_spin1.setValue(50.0)
    item1 = MagicMock()
    item1.text.return_value = "30000 руб"
    combo2 = MagicMock()
    combo2.currentText.return_value = "Продукт 3 - Медовый эль"
    volume_spin2 = QDoubleSpinBox()
    volume_spin2.setValue(20.0)
    item2 = MagicMock()
    item2.text.return_value = "14000 руб"
    # Увеличиваем side_effect до 8 элементов
    dialog.items_table.cellWidget.side_effect = [combo1, volume_spin1, combo2, volume_spin2, combo1, volume_spin1, combo2, volume_spin2]
    dialog.items_table.item.side_effect = [item1, item2]

    with patch.object(dialog, 'accept') as mock_accept:
        dialog.create_order()
        mock_accept.assert_called_once()

    order = session.query(Order).first()
    assert order is not None
    assert order.total_order_cost == 44000.0
    assert len(order.order_items) == 2
    updated_product1 = session.query(FinishedProduct).filter_by(product_id=1).first()
    updated_product3 = session.query(FinishedProduct).filter_by(product_id=3).first()
    assert updated_product1.available_volume == 100.0
    assert updated_product3.available_volume == 60.0

def test_edit_raw_material(clean_db):
    """Тест редактирования сырья"""
    session = clean_db
    raw_material = RawMaterial(name="Мед", quantity=250.0, cost=300.0, purchase_date="2025-01-15")
    session.add(raw_material)
    session.commit()

    dialog = EditRawMaterialDialog(material_id=raw_material.material_id)
    dialog.session = session
    # Убедимся, что self.material загружается
    dialog.material = session.query(RawMaterial).filter_by(material_id=raw_material.material_id).first()
    print(f"Material before update: {dialog.material.__dict__}")
    dialog.name_input = MagicMock()
    dialog.name_input.text.return_value = "Мед обновленный"
    dialog.quantity_spin = MagicMock()
    dialog.quantity_spin.value.return_value = 200.0
    dialog.cost_spin = MagicMock()
    dialog.cost_spin.value.return_value = 350.0
    dialog.purchase_date = MagicMock()
    dialog.purchase_date.date.return_value = QDate(2025, 1, 20)

    with patch.object(dialog, 'accept') as mock_accept:
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            dialog.save_material()
            mock_accept.assert_called_once()
            mock_warning.assert_not_called()

    updated_material = session.query(RawMaterial).filter_by(material_id=raw_material.material_id).first()
    print(f"Updated material: {updated_material.__dict__}")
    assert updated_material.name == "Мед обновленный"
    assert updated_material.quantity == 200.0
    assert updated_material.cost == 350.0
    assert updated_material.purchase_date == "2025-01-20"