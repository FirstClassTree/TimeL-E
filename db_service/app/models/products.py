# db_service/app/models/products.py

from sqlalchemy import Integer, String, ForeignKey, Numeric, Text
from app.models.base import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

class Department(Base):
    __tablename__ = 'departments'
    __table_args__ = {"schema": "products"}

    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department: Mapped[str] = mapped_column(String(100))

    # Enables accessing all products in this department
    products = relationship("Product", back_populates="department")

class Aisle(Base):
    __tablename__ = 'aisles'
    __table_args__ = {"schema": "products"}

    aisle_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aisle: Mapped[str] = mapped_column(String(100))

    # Enables accessing all products in this aisle
    products = relationship("Product", back_populates="aisle")

class Product(Base):
    __tablename__ = 'products'
    __table_args__ = {"schema": "products"}

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255))
    aisle_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.aisles.aisle_id'), index=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.departments.department_id'), index=True)

    # Enables accessing the department associated with the product
    department = relationship("Department", back_populates="products")

    # Enables accessing the aisle associated with the product
    aisle = relationship("Aisle", back_populates="products")

    # Enables accessing order items that reference this product
    order_items = relationship("OrderItem", back_populates="product")

class ProductEnriched(Base):
    __tablename__ = 'product_enriched'
    __table_args__ = {"schema": "products"}

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.products.product_id'), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship to the main product
    product = relationship("Product")
