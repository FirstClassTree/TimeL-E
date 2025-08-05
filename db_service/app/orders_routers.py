# app/orders_routers.py
import datetime
from fastapi import APIRouter, Query, HTTPException, status, Body, Path, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc, text
from sqlalchemy import Enum as SqlEnum
from .db_core.database import SessionLocal
import asyncpg
from .db_core.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User, OrderStatusHistory
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Generic, TypeVar
# Removed UUID imports since we're using integer user_ids and order_ids

router = APIRouter(prefix="/orders", tags=["orders"])

# Generic response model
T = TypeVar('T')

class ServiceResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] = []
    error: Optional[str] = None
    message: Optional[str] = None

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1

    # The order in which the item was added to the cart (useful for UI reordering, analytics, etc.)
    add_to_cart_order: Optional[int] = None

    reordered: int = 0

class EnrichedOrderItemData(BaseModel):
    """Order item with full product details"""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: int
    product_name: str
    quantity: int
    add_to_cart_order: int
    reordered: int
    price: Optional[float] = None  # From order_items.price
    
    # Product enrichment data
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    # Department/Aisle info
    department_name: Optional[str] = None
    aisle_name: Optional[str] = None

class OrderStatusHistoryData(BaseModel):
    """Order status change history"""
    model_config = ConfigDict(from_attributes=True)
    
    history_id: int
    order_id: str
    status: str  # The status the order changed to at this time
    changed_at: datetime.datetime
    changed_by: Optional[str] = None
    note: Optional[str] = None

class OrderSummaryData(BaseModel):
    """Simplified order data for list views"""
    model_config = ConfigDict(from_attributes=True)
    
    order_id: str
    user_id: str
    order_number: int
    total_items: int
    total_price: Optional[float] = None
    status: str
    delivery_name: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    items: List[EnrichedOrderItemData] = []

class OrderData(BaseModel):
    """Complete order data with all fields"""
    model_config = ConfigDict(from_attributes=True)
    
    order_id: str
    user_id: str
    order_number: int
    order_dow: Optional[int] = None
    order_hour_of_day: Optional[int] = None
    days_since_prior_order: Optional[int] = None
    total_items: int
    total_price: Optional[float] = None
    status: str
    delivery_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    items: List[EnrichedOrderItemData] = []

class DetailedOrderData(BaseModel):
    """Complete order data with status history and invoice for detailed view"""
    model_config = ConfigDict(from_attributes=True)
    
    order_id: str
    user_id: str
    order_number: int
    order_dow: Optional[int] = None
    order_hour_of_day: Optional[int] = None
    days_since_prior_order: Optional[int] = None
    total_items: int
    total_price: Optional[float] = None
    status: str
    delivery_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    invoice: Optional[bytes] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    items: List[EnrichedOrderItemData] = []
    status_history: List[OrderStatusHistoryData] = []

class CreateOrderRequest(BaseModel):
    user_id: str  # Accept external UUID4 from clients
    order_dow: Optional[int] = None
    order_hour_of_day: Optional[int] = None
    days_since_prior_order: Optional[int] = None
    total_items: Optional[int] = None
    # status is always "pending" for new orders - not configurable by client
    delivery_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    items: List[OrderItemRequest]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ServiceResponse[OrderData], status_code=status.HTTP_201_CREATED)
def create_order(order_request: CreateOrderRequest, session: Session = Depends(get_db)) -> ServiceResponse[OrderData]:
    try:
        # Convert external UUID4 to internal user ID
        user = session.query(User).filter(User.external_user_id == order_request.user_id).first()
        if not user:
            return ServiceResponse[OrderData](
                success=False,
                error="User not found",
                data=[]
            )
        
        # Set user context for order status trigger (use internal ID)
        session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": str(user.id)}
        )
        
        if not order_request.items:
            return ServiceResponse[OrderData](
                success=False,
                error="Order must contain at least one item",
                data=[]
            )

        # Validate all products exist
        product_ids = [item.product_id for item in order_request.items]
        existing_products = session.query(Product.product_id).filter(Product.product_id.in_(product_ids)).all()
        existing_product_ids = {p[0] for p in existing_products}
        missing_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]
        if missing_product_ids:
            return ServiceResponse[OrderData](
                success=False,
                error=f"Products not found: {', '.join(map(str, missing_product_ids))}",
                data=[]
            )

        # Get the most recent prior order by user (use internal user ID)
        last_order = session.execute(
            select(Order)
            .where(Order.user_id == user.id)
            .order_by(desc(Order.created_at))
            .limit(1)
        ).scalar_one_or_none()

        next_order_number = (last_order.order_number if last_order else 0) + 1

        days_since_prior_order = None
        if last_order:
            now = datetime.datetime.now(datetime.UTC)
            delta = now - last_order.created_at
            days_since_prior_order = int(delta.total_seconds() // 86400)  # in full days

        # Create order with internal user ID, let database auto-generate ID
        order = Order(
            user_id=user.id,  # Use internal user ID for FK
            order_number=next_order_number,
            order_dow=order_request.order_dow,
            order_hour_of_day=order_request.order_hour_of_day,
            days_since_prior_order=order_request.days_since_prior_order or days_since_prior_order,
            total_items=len(order_request.items),
            status=OrderStatus.PENDING,  # Always create orders with pending status
            delivery_name=order_request.delivery_name,
            phone_number=order_request.phone_number,
            street_address=order_request.street_address,
            city=order_request.city,
            postal_code=order_request.postal_code,
            country=order_request.country
            # tracking fields will be null for new orders; set later by fulfillment system
        )
        session.add(order)
        session.flush()  # Get the auto-generated order ID

        # Create order items
        order_items = [
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                add_to_cart_order=item.add_to_cart_order or (i + 1),
                reordered=item.reordered or 0
            )
            for i, item in enumerate(order_request.items)
        ]
        session.add_all(order_items)

        session.commit()
        session.refresh(order)  # Ensure order.items is populated

        # Build order data response
        order_data = OrderData(
            order_id=str(order.id),  # Return integer order ID as string
            user_id=str(user.external_user_id),  # Return external UUID4
            order_number=order.order_number,
            order_dow=order.order_dow,
            order_hour_of_day=order.order_hour_of_day,
            days_since_prior_order=order.days_since_prior_order,
            total_items=order.total_items,
            status=order.status.value,  # Convert enum to string
            delivery_name=order.delivery_name,
            phone_number=order.phone_number,
            street_address=order.street_address,
            city=order.city,
            postal_code=order.postal_code,
            country=order.country,
            tracking_number=order.tracking_number,
            shipping_carrier=order.shipping_carrier,
            tracking_url=order.tracking_url,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[
                EnrichedOrderItemData(
                    product_id=item.product_id,
                    product_name=item.product.product_name if item.product else "Unknown",
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order,
                    reordered=item.reordered,
                    price=item.price,
                    description=item.product.enriched.description if item.product and item.product.enriched else None,
                    image_url=item.product.enriched.image_url if item.product and item.product.enriched else None,
                    department_name=item.product.department.department if item.product and item.product.department else None,
                    aisle_name=item.product.aisle.aisle if item.product and item.product.aisle else None
                ) for item in order.items
            ]
        )
        
        return ServiceResponse[OrderData](
            success=True,
            message="Order created successfully",
            data=[order_data]
        )
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[OrderData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error creating order: {e}")
        return ServiceResponse[OrderData](
            success=False,
            error=f"Error creating order: {str(e)}",
            data=[]
        )

class AddOrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = 0
    reordered: int = 0

@router.post("/{order_id}/items", status_code=201)
def add_order_items(
    order_id: str = Path(...),
    items: List[AddOrderItemRequest] = Body(...),
    session: Session = Depends(get_db)
):
    try:
        # Get order by integer ID
        order = session.query(Order).filter(Order.id == int(order_id)).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            
        # Set user context for trigger (use internal user ID)
        session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": str(order.user_id)}
        )
        
        if not items:
            raise HTTPException(status_code=400, detail="Must provide at least one item")

        # Validate product IDs exist
        product_ids = [item.product_id for item in items]
        existing_products = session.query(Product.product_id).filter(Product.product_id.in_(product_ids)).all()
        existing_product_ids = {p[0] for p in existing_products}
        missing_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]
        if missing_product_ids:
            raise HTTPException(status_code=400, detail=f"Products not found: {', '.join(map(str, missing_product_ids))}")

        # Determine next add_to_cart_order (use internal order ID)
        current_count = session.query(OrderItem).filter_by(order_id=order.id).count()
        next_cart_order = current_count + 1

        # Add new order items
        added_items = []
        to_add = []

        existing_items = session.query(OrderItem).filter(
            OrderItem.order_id == order.id,  # Use internal order ID
            OrderItem.product_id.in_(product_ids)
        ).all()
        existing_map = {oi.product_id: oi for oi in existing_items}

        for item in items:
            if item.product_id in existing_map:
                existing = existing_map[item.product_id]
                # Update existing row
                existing.quantity += item.quantity
                # changes are tracked automatically by SQLAlchemy
                added_items.append({
                    "order_id": str(order.id),
                    "product_id": item.product_id,
                    "quantity": existing.quantity,
                    "add_to_cart_order": existing.add_to_cart_order,
                    "reordered": existing.reordered,
                    "updated": True
                })
            else:
                new_item = OrderItem(
                    order_id=order.id,  # Use internal order ID for FK
                    product_id=item.product_id,
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order or next_cart_order,
                    reordered=item.reordered or 0
                )
                to_add.append(new_item)
                added_items.append({
                    "order_id": str(order.id),
                    "product_id": new_item.product_id,
                    "quantity": new_item.quantity,
                    "add_to_cart_order": new_item.add_to_cart_order,
                    "reordered": new_item.reordered,
                    "updated": False
                })
                next_cart_order += 1

        # Bulk insert all new items at once
        if to_add:
            session.add_all(to_add)
        session.commit()
        return {
            "message": f"Added {len(added_items)} items to order {order_id}",
            "order_id": str(order.id),
            "added_items": added_items,
            "total_added": len(added_items)
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error adding order items: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding order items")

@router.get("/user/{user_id}", response_model=ServiceResponse[OrderSummaryData])
def get_user_orders(
    user_id: str, 
    limit: int = Query(20, description="Number of orders to return", ge=1, le=100),
    offset: int = Query(0, description="Number of orders to skip", ge=0),
    session: Session = Depends(get_db)
) -> ServiceResponse[OrderSummaryData]:
    """Get paginated order history for a specific user with enriched item details"""
    try:
        # Convert external UUID4 to internal user ID
        user = session.query(User).filter(User.external_user_id == user_id).first()
        if not user:
            return ServiceResponse[OrderSummaryData](
                success=False,
                error="User not found",
                data=[]
            )
        
        # Get paginated orders using SQLAlchemy relationships; proper pagination by orders
        orders = session.query(Order)\
                        .filter(Order.user_id == user.id)\
                        .order_by(Order.order_number.desc())\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        if not orders:
            return ServiceResponse[OrderSummaryData](
                success=True,
                message=f"No orders found for user {user_id}",
                data=[]
            )
        
        # Build response data using relationships
        orders_data = []
        for order in orders:
            # Build enriched items list using relationships
            items_data = []
            for item in order.items:  # Uses order_items relationship
                # Access product details through relationship
                product = item.product  # Uses product relationship
                enriched = product.enriched if product else None
                department = product.department if product else None
                aisle = product.aisle if product else None
                
                items_data.append(EnrichedOrderItemData(
                    product_id=item.product_id,
                    product_name=product.product_name if product else "Unknown Product",
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order,
                    reordered=item.reordered,
                    price=item.price,
                    description=enriched.description if enriched else None,
                    image_url=enriched.image_url if enriched else None,
                    department_name=department.department if department else None,
                    aisle_name=aisle.aisle if aisle else None
                ))
            
            # Build order summary data
            order_data = OrderSummaryData(
                order_id=str(order.id),
                user_id=str(user.external_user_id),  # Return external UUID4
                order_number=order.order_number,
                total_items=order.total_items,
                total_price=order.total_price,
                status=order.status.value,  # Convert enum to string
                delivery_name=order.delivery_name,
                created_at=order.created_at,
                updated_at=order.updated_at,
                items=items_data
            )
            orders_data.append(order_data)
        
        return ServiceResponse[OrderSummaryData](
            success=True,
            message=f"Found {len(orders_data)} orders for user {user_id}",
            data=orders_data
        )
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[OrderSummaryData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error fetching user orders: {e}")
        return ServiceResponse[OrderSummaryData](
            success=False,
            error=f"Error fetching user orders: {str(e)}",
            data=[]
        )

@router.get("/{order_id}", response_model=ServiceResponse[DetailedOrderData])
def get_order_details(
    order_id: str,
    session: Session = Depends(get_db)
) -> ServiceResponse[DetailedOrderData]:
    """Get detailed order information with full tracking info, enriched products, and status history"""
    try:
        # Get order by integer ID
        order = session.query(Order).filter(Order.id == int(order_id)).first()
        if not order:
            return ServiceResponse[DetailedOrderData](
                success=False,
                error="Order not found",
                data=[]
            )
        
        # Get user for external UUID4
        user = order.user
        
        # Build enriched items list using relationships
        items_data = []
        for item in order.items:  # Uses order_items relationship
            # Access product details through relationship
            product = item.product  # Uses product relationship
            enriched = product.enriched if product else None
            department = product.department if product else None
            aisle = product.aisle if product else None
            
            items_data.append(EnrichedOrderItemData(
                product_id=item.product_id,
                product_name=product.product_name if product else "Unknown Product",
                quantity=item.quantity,
                add_to_cart_order=item.add_to_cart_order,
                reordered=item.reordered,
                price=item.price,
                description=enriched.description if enriched else None,
                image_url=enriched.image_url if enriched else None,
                department_name=department.department if department else None,
                aisle_name=aisle.aisle if aisle else None
            ))
        
        # Get order status history
        status_history = session.query(OrderStatusHistory)\
                               .filter(OrderStatusHistory.order_id == order.id)\
                               .order_by(OrderStatusHistory.changed_at.asc())\
                               .all()
        
        history_data = []
        for history in status_history:
            history_data.append(OrderStatusHistoryData(
                history_id=history.history_id,
                order_id=str(order.id),
                status=history.new_status.value if history.new_status else "unknown",
                changed_at=history.changed_at,
                changed_by=str(history.changed_by) if history.changed_by else None,
                note=history.note
            ))
        
        # Build detailed order data
        order_data = DetailedOrderData(
            order_id=str(order.id),
            user_id=str(user.external_user_id),  # Return external UUID4
            order_number=order.order_number,
            order_dow=order.order_dow,
            order_hour_of_day=order.order_hour_of_day,
            days_since_prior_order=order.days_since_prior_order,
            total_items=order.total_items,
            total_price=order.total_price,
            status=order.status.value,  # Convert enum to string
            delivery_name=order.delivery_name,
            phone_number=order.phone_number,
            street_address=order.street_address,
            city=order.city,
            postal_code=order.postal_code,
            country=order.country,
            tracking_number=order.tracking_number,
            shipping_carrier=order.shipping_carrier,
            tracking_url=order.tracking_url,
            invoice=order.invoice,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items_data,
            status_history=history_data
        )
        
        return ServiceResponse[DetailedOrderData](
            success=True,
            message=f"Order {order_id} details retrieved successfully",
            data=[order_data]
        )
        
    except ValueError:
        return ServiceResponse[DetailedOrderData](
            success=False,
            error="Invalid order ID format",
            data=[]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[DetailedOrderData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error fetching order details: {e}")
        return ServiceResponse[DetailedOrderData](
            success=False,
            error=f"Error fetching order details: {str(e)}",
            data=[]
        )

@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: str, session: Session = Depends(get_db)):
    try:
        # Get order by integer ID
        order = session.query(Order).filter(Order.id == int(order_id)).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        session.delete(order)
        session.commit()
        return {"message": "Order deleted successfully", "order_id": order_id}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error deleting order: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting order")
