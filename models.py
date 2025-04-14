from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
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

class OrderStatus(PyEnum):
    PENDING = "В ожидании"
    COMPLETED = "Выполнен"

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # Будем хранить строковое представление Enum
    batches = relationship("Batch", back_populates="user")
    orders = relationship("Order", back_populates="user")

class RawMaterial(Base):
    __tablename__ = 'raw_materials'
    material_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    purchase_date = Column(String(10), nullable=False)
    batch_materials = relationship("BatchMaterial", back_populates="material")

class Recipe(Base):
    __tablename__ = 'recipes'
    recipe_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    batches = relationship("Batch", back_populates="recipe")

class Batch(Base):
    __tablename__ = 'batches'
    batch_id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.recipe_id'), nullable=False)
    volume = Column(Float, nullable=False)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)  # Будем хранить строковое представление Enum
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    price_per_liter = Column(Float, nullable=False)
    recipe = relationship("Recipe", back_populates="batches")
    user = relationship("User", back_populates="batches")
    batch_materials = relationship("BatchMaterial", back_populates="batch")
    finished_product = relationship("FinishedProduct", back_populates="batch", uselist=False)

class BatchMaterial(Base):
    __tablename__ = 'batch_materials'
    batch_id = Column(Integer, ForeignKey('batches.batch_id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('raw_materials.material_id'), primary_key=True)
    used_quantity = Column(Float, nullable=False)
    batch = relationship("Batch", back_populates="batch_materials")
    material = relationship("RawMaterial", back_populates="batch_materials")

class FinishedProduct(Base):
    __tablename__ = 'finished_products'
    product_id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.batch_id'), nullable=False, unique=True)
    volume = Column(Float, nullable=False)
    available_volume = Column(Float, nullable=False)
    production_date = Column(String(10), nullable=False)
    price_per_liter = Column(Float, nullable=False)
    batch = relationship("Batch", back_populates="finished_product")
    order_items = relationship("OrderItem", back_populates="product")

class Client(Base):
    __tablename__ = 'clients'
    client_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)  # Будем хранить строковое представление Enum
    contact = Column(String(100), nullable=False)
    inn = Column(String(12))
    orders = relationship("Order", back_populates="client")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    order_date = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)  # Будем хранить строковое представление Enum
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    total_order_cost = Column(Float, nullable=False)
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
engine = create_engine('sqlite:///honey_drinks.db', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)