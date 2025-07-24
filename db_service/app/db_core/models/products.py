# db_service/app/db_core/models/products.py


"""
products.py

SQLAlchemy ORM models for the products schema, including departments, aisles,
products, and enriched product data. Models define business logic constraints, relationships,
and metadata for use in API, admin, and business logic layers.

OpenAPI Description:
    Provides structured representation and relationships for product catalog,
    supporting inventory, categorization, and enrichment with additional metadata.
"""

from sqlalchemy import Integer, String, ForeignKey, Numeric, Text
from ..models.base import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List

class Department(Base):
    """
    Product department (e.g., 'Bakery', 'Produce').

    Attributes:
        department_id (int): Primary key.
        department (str): Name of department.

    Relationships:
        - products: All products in this department.

    OpenAPI Description:
        Catalog table for product departments/categories.
    """
    __tablename__ = 'departments'
    __table_args__ = {"schema": "products"}

    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Enables accessing all products in this department
    products: Mapped[list["Product"]] = relationship("Product", back_populates="department")

class Aisle(Base):
    """
    Product aisle (e.g., 'Baking Ingredients', 'Fresh Herbs').

    Attributes:
        aisle_id (int): Primary key.
        aisle (str): Name of aisle.

    Relationships:
        - products: All products in this aisle.

    OpenAPI Description:
        Catalog table for physical or logical product aisles.
    """
    __tablename__ = 'aisles'
    __table_args__ = {"schema": "products"}

    aisle_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    aisle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Enables accessing all products in this aisle
    products: Mapped[list["Product"]] = relationship("Product", back_populates="aisle")

class Product(Base):
    """
    Master table for products.

    Attributes:
        product_id (int): Primary key.
        product_name (str): Name of product.
        aisle_id (int): Foreign key to aisle.
        department_id (int): Foreign key to department.

    Relationships:
        - department: Department to which product belongs.
        - aisle: Aisle to which product belongs.
        - order_items: Order items containing this product.
        - enriched: Enriched product metadata (one-to-one relationship).

    OpenAPI Description:
        Products available in the catalog, with classification by aisle and department.
    """
    __tablename__ = 'products'
    __table_args__ = {"schema": "products"}

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    aisle_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.aisles.aisle_id'), index=True, nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.departments.department_id'), index=True, nullable=False)

    # Enables accessing the department associated with the product
    department: Mapped["Department"] = relationship("Department", back_populates="products")

    # Enables accessing the aisle associated with the product
    aisle: Mapped["Aisle"] = relationship("Aisle", back_populates="products")

    # Enables accessing order items that reference this product
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    enriched: Mapped[Optional["ProductEnriched"]] = relationship("ProductEnriched", uselist=False, back_populates="product")

class ProductEnriched(Base):
    """
    Enriched metadata for a product.

    Attributes:
        product_id (int): Product primary key (FK).
        description (str): Optional human-friendly description.
        price (float): Price of product. Defaults to 0.00.
        image_url (str): Optional image URL.

    Relationships:
        - product: Main Product object (one-to-one relationship).

    OpenAPI Description:
        Additional metadata for products, including description, price, and imagery.
    """
    __tablename__ = 'product_enriched'
    __table_args__ = {"schema": "products"}

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.products.product_id'), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0.00, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship to the main product
    product: Mapped["Product"] = relationship("Product", back_populates="enriched")

