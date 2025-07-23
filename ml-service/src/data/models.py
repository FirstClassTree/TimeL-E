# ml-service/src/data/models.py
# Database models for ML service

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id = Column(String, primary_key=True)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_metadata = Column(JSON)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "orders"}
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("public.users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    
    # Relationships
    user = relationship("User")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {"schema": "orders"}
    
    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.orders.id"))
    product_id = Column(Integer, ForeignKey("products.products.product_id"))
    quantity = Column(Integer)
    price = Column(Float)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "products"}
    
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String)
    aisle_id = Column(Integer, ForeignKey("products.aisles.aisle_id"))
    department_id = Column(Integer, ForeignKey("products.departments.department_id"))
    
    # Relationships
    aisle = relationship("Aisle")
    department = relationship("Department")

class Aisle(Base):
    __tablename__ = "aisles"
    __table_args__ = {"schema": "products"}
    
    aisle_id = Column(Integer, primary_key=True)
    aisle = Column(String)

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "products"}
    
    department_id = Column(Integer, primary_key=True)
    department = Column(String)

# Alias for compatibility
Category = Department
