# Import all model classes to ensure they are registered with metadata
from app.models.users import User
from app.models.products import Product, Department, Aisle
from app.models.orders import Order, OrderItem