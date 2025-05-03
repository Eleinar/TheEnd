from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum as PyEnum

Base = declarative_base()

# Определение перечислений
class UserRole(PyEnum):
    ENTREPRENEUR = "Предприниматель"
    TECHNOLOGIST = "Технолог"
    ASSISTANT = "Помощник"
    ADMIN = "Администратор"

class BatchStatus(PyEnum):
    FERMENTING = "В брожении"
    READY = "Готова"

class ClientType(PyEnum):
    INDIVIDUAL = "Физлицо"
    LEGAL_ENTITY = "Юрлицо"
    ENTREPRENEUR = "ИП"

class OrderStatus(PyEnum):
    PENDING = "Выполняется"
    COMPLETED = "Выполнен"
    FINISHED = "Завершен"

class Unit(PyEnum):
    KG = "кг"
    LITER = "л"

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # Строковое представление Enum UserRole
    batches = relationship("Batch", back_populates="user")
    orders = relationship("Order", back_populates="user")

class RawMaterial(Base):
    __tablename__ = 'raw_materials'
    material_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(10), nullable=False)  # Добавлено для единиц измерения
    cost = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)  # Изменено на Date
    min_quantity = Column(Float, default=0)  # Добавлено для порога запасов
    batch_materials = relationship("BatchMaterial", back_populates="material")
    recipe_materials = relationship("RecipeMaterial", back_populates="material")

class Recipe(Base):
    __tablename__ = 'recipes'
    recipe_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)  # Изменено на Text
    batches = relationship("Batch", back_populates="recipe")
    recipe_materials = relationship("RecipeMaterial", back_populates="recipe")

class RecipeMaterial(Base):
    __tablename__ = 'recipe_materials'
    recipe_id = Column(Integer, ForeignKey('recipes.recipe_id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('raw_materials.material_id'), primary_key=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(10), nullable=False)  # Единица измерения
    recipe = relationship("Recipe", back_populates="recipe_materials")
    material = relationship("RawMaterial", back_populates="recipe_materials")

class Client(Base):
    __tablename__ = 'clients'
    client_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)  # Строковое представление Enum ClientType
    contact = Column(String(100), nullable=False)
    inn = Column(String(12))
    address = Column(String(255))  # Добавлено для адреса доставки
    orders = relationship("Order", back_populates="client")

class Batch(Base):
    __tablename__ = 'batches'
    batch_id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.recipe_id'), nullable=False)
    volume = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)  # Изменено на Date
    end_date = Column(Date, nullable=False)  # Изменено на Date
    status = Column(String(20), nullable=False)  # Строковое представление Enum BatchStatus
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    price_per_liter = Column(Float, nullable=False, default=500.0)
    comments = Column(Text)  # Добавлено для заметок
    recipe = relationship("Recipe", back_populates="batches")
    user = relationship("User", back_populates="batches")
    batch_materials = relationship("BatchMaterial", back_populates="batch")
    finished_product = relationship("FinishedProduct", back_populates="batch", uselist=False)

class BatchMaterial(Base):
    __tablename__ = 'batch_materials'
    batch_id = Column(Integer, ForeignKey('batches.batch_id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('raw_materials.material_id'), primary_key=True)
    used_quantity = Column(Float, nullable=False)
    used_date = Column(Date)  # Добавлено для даты использования
    batch = relationship("Batch", back_populates="batch_materials")
    material = relationship("RawMaterial", back_populates="batch_materials")

class FinishedProduct(Base):
    __tablename__ = 'finished_products'
    product_id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.batch_id'), nullable=False, unique=True)
    volume = Column(Float, nullable=False)
    available_volume = Column(Float, nullable=False)
    production_date = Column(Date, nullable=False)  # Изменено на Date
    expiration_date = Column(Date)  # Добавлено для срока годности
    price_per_liter = Column(Float, nullable=False)
    batch = relationship("Batch", back_populates="finished_product")
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    order_date = Column(Date, nullable=False)  # Изменено на Date
    delivery_date = Column(Date)  # Добавлено для даты доставки
    status = Column(String(20), nullable=False)  # Строковое представление Enum OrderStatus
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    total_order_cost = Column(Float, nullable=False)
    comments = Column(Text)  # Добавлено для заметок
    client = relationship("Client", back_populates="orders")
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'
    item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('finished_products.product_id'), nullable=False)
    volume = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    order = relationship("Order", back_populates="order_items")
    product = relationship("FinishedProduct", back_populates="order_items")

# Подключение к базе и создание таблиц
engine = create_engine('postgresql://postgres:p0sTgr3s@82.202.138.183:5432/postgres', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)