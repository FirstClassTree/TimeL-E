# backend/app/services/database_service.py
from typing import Dict, Any, Optional, List
from .base_client import ServiceClient
from ..config import settings

class DatabaseService:
    """Database service client"""
    
    def __init__(self):
        self.base_url = settings.DB_SERVICE_URL
    
    # Generic CRUD operations
    async def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity in database"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/{entity_type}",
                data=data
            )
    
    async def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Get entity from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/{entity_type}/{entity_id}"
            )
    
    async def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity in database"""
        async with ServiceClient() as client:
            return await client.request(
                method="PUT",
                url=f"{self.base_url}/{entity_type}/{entity_id}",
                data=data
            )
    
    async def delete_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Delete entity from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="DELETE",
                url=f"{self.base_url}/{entity_type}/{entity_id}"
            )
    
    async def list_entities(self, entity_type: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List entities from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/{entity_type}",
                params=filters
            )
    
    async def query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom query"""
        async with ServiceClient() as client:
            response = await client.request(
                method="POST",
                url=f"{self.base_url}/query",
                data=query_data
            )
            
            # Convert db-service response format to expected backend format
            if response.get("status") == "ok":
                return {
                    "success": True,
                    "data": response.get("results", [])
                }
            else:
                return {
                    "success": False,
                    "data": [],
                    "error": response.get("detail", "Query failed")
                }

    # Product-specific methods
    async def get_products_with_filters(
        self, 
        limit: int = 50, 
        offset: int = 0,
        categories: Optional[List[str]] = None,
        department_id: Optional[int] = None,
        aisle_id: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products with filtering and pagination"""
        query = {
            "sql": """
                SELECT p.product_id, p.product_name, p.aisle_id, p.department_id,
                       d.department as department_name, a.aisle as aisle_name,
                       pe.description, pe.price, pe.image_url
                FROM products.products p
                JOIN products.departments d ON p.department_id = d.department_id
                JOIN products.aisles a ON p.aisle_id = a.aisle_id
                LEFT JOIN products.product_enriched pe ON p.product_id = pe.product_id
                WHERE 1=1
            """,
            "params": []
        }
        
        param_count = 1
        
        if department_id:
            query["sql"] += f" AND p.department_id = ${param_count}"
            query["params"].append(department_id)
            param_count += 1
            
        if aisle_id:
            query["sql"] += f" AND p.aisle_id = ${param_count}"
            query["params"].append(aisle_id)
            param_count += 1
            
        if categories:
            # Filter by department names
            placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(categories))])
            query["sql"] += f" AND d.department IN ({placeholders})"
            query["params"].extend(categories)
            param_count += len(categories)
            
        if search_query:
            query["sql"] += f" AND LOWER(p.product_name) LIKE LOWER(${param_count})"
            query["params"].append(f"%{search_query}%")
            param_count += 1
        
        query["sql"] += f" ORDER BY p.product_id LIMIT ${param_count} OFFSET ${param_count + 1}"
        query["params"].extend([limit, offset])
        
        return await self.query(query)

    async def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID with joined data"""
        query = {
            "sql": """
                SELECT p.product_id, p.product_name, p.aisle_id, p.department_id,
                       d.department as department_name, a.aisle as aisle_name,
                       pe.description, pe.price, pe.image_url
                FROM products.products p
                JOIN products.departments d ON p.department_id = d.department_id
                JOIN products.aisles a ON p.aisle_id = a.aisle_id
                LEFT JOIN products.product_enriched pe ON p.product_id = pe.product_id
                WHERE p.product_id = $1
            """,
            "params": [product_id]
        }
        return await self.query(query)

    async def get_products_by_department(self, department_id: int) -> Dict[str, Any]:
        """Get all products in a department"""
        query = {
            "sql": """
                SELECT p.product_id, p.product_name, p.aisle_id, p.department_id,
                       d.department as department_name, a.aisle as aisle_name,
                       pe.description, pe.price, pe.image_url
                FROM products.products p
                JOIN products.departments d ON p.department_id = d.department_id
                JOIN products.aisles a ON p.aisle_id = a.aisle_id
                LEFT JOIN products.product_enriched pe ON p.product_id = pe.product_id
                WHERE p.department_id = $1
                ORDER BY p.product_name
            """,
            "params": [department_id]
        }
        return await self.query(query)

    async def get_products_by_aisle(self, aisle_id: int) -> Dict[str, Any]:
        """Get all products in an aisle"""
        query = {
            "sql": """
                SELECT p.product_id, p.product_name, p.aisle_id, p.department_id,
                       d.department as department_name, a.aisle as aisle_name,
                       pe.description, pe.price, pe.image_url
                FROM products.products p
                JOIN products.departments d ON p.department_id = d.department_id
                JOIN products.aisles a ON p.aisle_id = a.aisle_id
                LEFT JOIN products.product_enriched pe ON p.product_id = pe.product_id
                WHERE p.aisle_id = $1
                ORDER BY p.product_name
            """,
            "params": [aisle_id]
        }
        return await self.query(query)

    async def get_aisle_by_id(self, aisle_id: int) -> Dict[str, Any]:
        """Get aisle by ID"""
        query = {
            "sql": "SELECT * FROM products.aisles WHERE aisle_id = $1",
            "params": [aisle_id]
        }
        return await self.query(query)

    # Department-specific methods
    async def get_all_departments(self) -> Dict[str, Any]:
        """Get all departments"""
        query = {
            "sql": "SELECT department_id, department FROM products.departments ORDER BY department",
            "params": []
        }
        return await self.query(query)

    async def get_department_by_id(self, department_id: int) -> Dict[str, Any]:
        """Get department by ID"""
        query = {
            "sql": "SELECT department_id, department FROM products.departments WHERE department_id = $1",
            "params": [department_id]
        }
        return await self.query(query)

    # Order-specific methods
    async def get_user_orders_with_filters(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get user orders with filtering and pagination"""
        query = {
            "sql": """
                SELECT o.order_id, o.user_id, o.eval_set, o.order_number, 
                       o.order_dow, o.order_hour_of_day, o.days_since_prior_order,
                       o.total_items, o.status::text, o.phone_number, o.street_address, 
                       o.city, o.postal_code, o.country, o.tracking_number, 
                       o.shipping_carrier, o.tracking_url
                FROM orders.orders o
                WHERE o.user_id = $1
            """,
            "params": [user_id]
        }
        
        param_count = 2
        
        if status:
            query["sql"] += f" AND o.status = ${param_count}::order_status_enum"
            query["params"].append(status.upper())
            param_count += 1
        
        order_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        query["sql"] += f" ORDER BY o.order_number {order_direction} LIMIT ${param_count} OFFSET ${param_count + 1}"
        query["params"].extend([limit, offset])
        
        return await self.query(query)

    async def get_order_with_items(self, order_id: str) -> Dict[str, Any]:
        """Get order with all its items"""
        query = {
            "sql": """
                SELECT o.order_id, o.user_id, o.eval_set, o.order_number, 
                       o.order_dow, o.order_hour_of_day, o.days_since_prior_order,
                       o.total_items, o.status::text, o.phone_number, o.street_address, 
                       o.city, o.postal_code, o.country, o.tracking_number, 
                       o.shipping_carrier, o.tracking_url,
                       oi.product_id, oi.add_to_cart_order, oi.reordered, oi.quantity,
                       p.product_name
                FROM orders.orders o
                LEFT JOIN orders.order_items oi ON o.order_id = oi.order_id
                LEFT JOIN products.products p ON oi.product_id = p.product_id
                WHERE o.order_id = $1
                ORDER BY oi.add_to_cart_order
            """,
            "params": [order_id]
        }
        return await self.query(query)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Get order basic info"""
        query = {
            "sql": """
                SELECT o.order_id, o.user_id, o.eval_set, o.order_number, 
                       o.order_dow, o.order_hour_of_day, o.days_since_prior_order,
                       o.total_items, o.status::text, o.phone_number, o.street_address, 
                       o.city, o.postal_code, o.country, o.tracking_number, 
                       o.shipping_carrier, o.tracking_url
                FROM orders.orders o
                WHERE o.order_id = $1
            """,
            "params": [order_id]
        }
        return await self.query(query)

    async def get_order_items(self, order_id: str) -> Dict[str, Any]:
        """Get items for a specific order"""
        query = {
            "sql": """
                SELECT oi.order_id, oi.product_id, oi.add_to_cart_order, 
                       oi.reordered, oi.quantity, p.product_name
                FROM orders.order_items oi
                JOIN products.products p ON oi.product_id = p.product_id
                WHERE oi.order_id = $1
                ORDER BY oi.add_to_cart_order
            """,
            "params": [order_id]
        }
        return await self.query(query)

    async def update_order_status(self, order_id: str, status: str) -> Dict[str, Any]:
        """Update order status"""
        query = {
            "sql": """
                UPDATE orders.orders 
                SET status = $2::order_status_enum
                WHERE order_id = $1
                RETURNING order_id, status::text
            """,
            "params": [order_id, status.upper()]
        }
        return await self.query(query)

    async def get_order_invoice(self, order_id: str) -> Dict[str, Any]:
        """Get order invoice data"""
        query = {
            "sql": "SELECT order_id, invoice FROM orders.orders WHERE order_id = $1",
            "params": [order_id]
        }
        return await self.query(query)

    # User-specific methods
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        query = {
            "sql": """
                SELECT user_id, name, email_address, phone_number, 
                       street_address, city, postal_code, country
                FROM users.users WHERE user_id = $1
            """,
            "params": [int(user_id)]
        }
        return await self.query(query)

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        query = {
            "sql": """
                INSERT INTO users.users (name, hashed_password, email_address, 
                                       phone_number, street_address, city, postal_code, country)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING user_id, name, email_address
            """,
            "params": [
                user_data["name"],
                user_data["hashed_password"],
                user_data["email_address"],
                user_data["phone_number"],
                user_data["street_address"],
                user_data["city"],
                user_data["postal_code"],
                user_data["country"]
            ]
        }
        return await self.query(query)

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user details"""
        # Build dynamic update query based on provided fields
        set_clauses = []
        params = [int(user_id)]
        param_count = 2
        
        for field in ["name", "email_address", "phone_number", "street_address", "city", "postal_code", "country"]:
            if field in user_data:
                set_clauses.append(f"{field} = ${param_count}")
                params.append(user_data[field])
                param_count += 1
        
        if not set_clauses:
            raise ValueError("No fields to update")
        
        query = {
            "sql": f"""
                UPDATE users.users 
                SET {", ".join(set_clauses)}
                WHERE user_id = $1
                RETURNING user_id, name, email_address
            """,
            "params": params
        }
        return await self.query(query)

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete user"""
        query = {
            "sql": "DELETE FROM users.users WHERE user_id = $1 RETURNING user_id",
            "params": [int(user_id)]
        }
        return await self.query(query)

    async def update_user_password(self, user_id: str, hashed_password: str) -> Dict[str, Any]:
        """Update user password"""
        query = {
            "sql": """
                UPDATE users.users 
                SET hashed_password = $2
                WHERE user_id = $1
                RETURNING user_id
            """,
            "params": [int(user_id), hashed_password]
        }
        return await self.query(query)

# Service instance
db_service = DatabaseService()
