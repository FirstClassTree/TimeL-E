# backend/app/routers/orders.py
from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional
from ..models.base import APIResponse
from ..models.grocery import Order, OrderWithItems, CreateOrderRequest, OrderItem
from ..services.database_service import db_service

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_orders(
    user_id: str,
    limit: int = Query(50, description="Number of orders to return", ge=1, le=100),
    offset: int = Query(0, description="Number of orders to skip", ge=0),
    status: Optional[str] = Query(None, description="Filter by order status"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'")
) -> APIResponse:
    """Get orders for a specific user with filtering and pagination"""
    try:
        # Get orders from database
        db_result = await db_service.get_user_orders_with_filters(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status,
            sort_order=sort
        )
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        orders_data = db_result.get("data", [])
        
        if not orders_data:
            return APIResponse(
                message=f"No orders found for user {user_id}",
                data={"orders": [], "total": 0}
            )
        
        # Convert to Order models and include order items
        orders_with_items = []
        for order_row in orders_data:
            # Get items for this order
            items_result = await db_service.get_order_items(str(order_row["order_id"]))
            items_data = items_result.get("data", []) if items_result.get("success", True) else []
            
            # Convert items to OrderItem models
            items = [
                OrderItem(
                    order_id=str(item["order_id"]),
                    product_id=item["product_id"],
                    add_to_cart_order=item["add_to_cart_order"],
                    reordered=item["reordered"],
                    quantity=item["quantity"],
                    product_name=item.get("product_name")
                )
                for item in items_data
            ]
            
            # Create order with items
            order_with_items = {
                "order_id": str(order_row["order_id"]),
                "user_id": str(order_row["user_id"]),
                "eval_set": order_row["eval_set"],
                "order_number": order_row["order_number"],
                "order_dow": order_row["order_dow"],
                "order_hour_of_day": order_row["order_hour_of_day"],
                "days_since_prior_order": order_row.get("days_since_prior_order"),
                "total_items": order_row["total_items"],
                "status": order_row["status"],
                "items": items,
                "item_count": len(items),
                # Include delivery/tracking info
                "phone_number": order_row.get("phone_number"),
                "street_address": order_row.get("street_address"),
                "city": order_row.get("city"),
                "postal_code": order_row.get("postal_code"),
                "country": order_row.get("country"),
                "tracking_number": order_row.get("tracking_number"),
                "shipping_carrier": order_row.get("shipping_carrier"),
                "tracking_url": order_row.get("tracking_url")
            }
            orders_with_items.append(order_with_items)
        
        return APIResponse(
            message=f"Found {len(orders_with_items)} orders for user {user_id}",
            data={
                "orders": orders_with_items,
                "total": len(orders_with_items),
                "page": (offset // limit) + 1,
                "per_page": limit,
                "has_next": len(orders_with_items) == limit,
                "has_prev": offset > 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=APIResponse)
async def get_order(order_id: str) -> APIResponse:
    """Get specific order with all its items"""
    try:
        # Get order with items from database
        db_result = await db_service.get_order_with_items(order_id)
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        orders_data = db_result.get("data", [])
        
        if not orders_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # Group the data (SQL JOIN returns multiple rows for order with items)
        order_info = None
        items = []
        
        for row in orders_data:
            if order_info is None:
                order_info = {
                    "order_id": str(row["order_id"]),
                    "user_id": str(row["user_id"]),
                    "eval_set": row["eval_set"],
                    "order_number": row["order_number"],
                    "order_dow": row["order_dow"],
                    "order_hour_of_day": row["order_hour_of_day"],
                    "days_since_prior_order": row.get("days_since_prior_order"),
                    "total_items": row["total_items"],
                    "status": row["status"],
                    "phone_number": row.get("phone_number"),
                    "street_address": row.get("street_address"),
                    "city": row.get("city"),
                    "postal_code": row.get("postal_code"),
                    "country": row.get("country"),
                    "tracking_number": row.get("tracking_number"),
                    "shipping_carrier": row.get("shipping_carrier"),
                    "tracking_url": row.get("tracking_url")
                }
            
            # Add item if it exists (LEFT JOIN might have NULL items)
            if row.get("product_id"):
                item = OrderItem(
                    order_id=str(row["order_id"]),
                    product_id=row["product_id"],
                    add_to_cart_order=row["add_to_cart_order"],
                    reordered=row["reordered"],
                    quantity=row["quantity"],
                    product_name=row.get("product_name")
                )
                items.append(item)
        
        order_with_items = OrderWithItems(
            **order_info,
            items=items,
            total_items=len(items)
        )
        
        return APIResponse(
            message="Order retrieved successfully",
            data=order_with_items
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/items", response_model=APIResponse)
async def get_order_items(order_id: str) -> APIResponse:
    """Get items for a specific order"""
    try:
        # Verify order exists
        order_result = await db_service.get_order_by_id(order_id)
        
        if not order_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        order_data = order_result.get("data", [])
        
        if not order_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # Get order items
        items_result = await db_service.get_order_items(order_id)
        
        if not items_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        items_data = items_result.get("data", [])
        
        # Convert to OrderItem models
        items = [
            OrderItem(
                order_id=str(item["order_id"]),
                product_id=item["product_id"],
                add_to_cart_order=item["add_to_cart_order"],
                reordered=item["reordered"],
                quantity=item["quantity"],
                product_name=item.get("product_name")
            )
            for item in items_data
        ]
        
        return APIResponse(
            message=f"Found {len(items)} items in order {order_id}",
            data={
                "order_id": order_id,
                "items": items,
                "total_items": len(items)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=APIResponse)
async def create_order(order_request: CreateOrderRequest) -> APIResponse:
    """Create a new order"""
    try:
        if not order_request.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        
        # Validate user exists
        user_result = await db_service.get_user_by_id(str(order_request.user_id))
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=400, detail=f"User {order_request.user_id} not found")
        
        # Validate all products exist
        for item in order_request.items:
            product_id = item.get("product_id")
            if not product_id:
                raise HTTPException(status_code=400, detail="Product ID is required")
                
            product_result = await db_service.get_product_by_id(product_id)
            if not product_result.get("success", True) or not product_result.get("data", []):
                raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
        
        # TODO: Implement actual order creation in database
        # For now, return a mock response indicating the order would be created
        
        mock_order = {
            "order_id": "new-order-uuid",  # Would be generated by database
            "user_id": str(order_request.user_id),
            # "eval_set": "new",
            "order_number": 1,  # Would calculate based on user's order history
            "order_dow": 1,     # Monday
            "order_hour_of_day": 14,  # 2 PM
            "days_since_prior_order": None,
            "total_items": len(order_request.items),
            "status": "pending",
            "items": [
                {
                    "product_id": item["product_id"],
                    "quantity": item.get("quantity", 1),
                    "add_to_cart_order": i + 1,
                    "reordered": 0
                }
                for i, item in enumerate(order_request.items)
            ]
        }
        
        return APIResponse(
            message="Order created successfully",
            data=mock_order
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/items", response_model=APIResponse)
async def add_order_items(order_id: str, items: List[dict]) -> APIResponse:
    """Add items to an existing order"""
    try:
        # Verify order exists
        order_result = await db_service.get_order_by_id(order_id)
        
        if not order_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        order_data = order_result.get("data", [])
        
        if not order_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if not items:
            raise HTTPException(status_code=400, detail="Must provide at least one item")
        
        # Validate products exist
        for item in items:
            product_id = item.get("product_id")
            if not product_id:
                raise HTTPException(status_code=400, detail="Product ID is required")
                
            product_result = await db_service.get_product_by_id(product_id)
            if not product_result.get("success", True) or not product_result.get("data", []):
                raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
        
        # Get current items to determine next add_to_cart_order
        current_items_result = await db_service.get_order_items(order_id)
        current_items = current_items_result.get("data", []) if current_items_result.get("success", True) else []
        next_cart_order = len(current_items) + 1
        
        # TODO: Implement actual item addition to database
        # For now, return a mock response
        
        added_items = []
        for item in items:
            added_items.append({
                "order_id": order_id,
                "product_id": item["product_id"],
                "add_to_cart_order": next_cart_order,
                "reordered": 0,
                "quantity": item.get("quantity", 1)
            })
            next_cart_order += 1
        
        return APIResponse(
            message=f"Added {len(added_items)} items to order {order_id}",
            data={
                "order_id": order_id,
                "added_items": added_items,
                "total_added": len(added_items)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New enhanced endpoints

@router.post("/{order_id}/cancel", response_model=APIResponse)
async def cancel_order(order_id: str) -> APIResponse:
    """Cancel an order"""
    try:
        # Update order status to cancelled
        result = await db_service.update_order_status(order_id, "CANCELLED")
        
        if not result.get("success", True):
            raise HTTPException(status_code=500, detail="Failed to cancel order")
        
        updated_data = result.get("data", [])
        
        if not updated_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return APIResponse(
            message=f"Order {order_id} has been cancelled",
            data={
                "order_id": order_id,
                "status": "cancelled",
                "updated_at": "now"  # Would include actual timestamp
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/tracking", response_model=APIResponse)
async def get_order_tracking(order_id: str) -> APIResponse:
    """Get tracking information for an order"""
    try:
        # Get order with tracking info
        order_result = await db_service.get_order_by_id(order_id)
        
        if not order_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        order_data = order_result.get("data", [])
        
        if not order_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        order = order_data[0]
        
        tracking_info = {
            "order_id": order_id,
            "status": order["status"],
            "tracking_number": order.get("tracking_number"),
            "shipping_carrier": order.get("shipping_carrier"),
            "tracking_url": order.get("tracking_url"),
            "delivery_address": {
                "street_address": order.get("street_address"),
                "city": order.get("city"),
                "postal_code": order.get("postal_code"),
                "country": order.get("country")
            }
        }
        
        return APIResponse(
            message="Tracking information retrieved successfully",
            data=tracking_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/invoice", response_model=APIResponse)
async def get_order_invoice(order_id: str) -> APIResponse:
    """Get invoice for an order"""
    try:
        # Get order invoice
        invoice_result = await db_service.get_order_invoice(order_id)
        
        if not invoice_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        invoice_data = invoice_result.get("data", [])
        
        if not invoice_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        invoice_info = invoice_data[0]
        
        if not invoice_info.get("invoice"):
            raise HTTPException(status_code=404, detail=f"No invoice available for order {order_id}")
        
        # In a real implementation, you would:
        # 1. Return the binary data as a file download
        # 2. Set appropriate content-type headers
        # For now, return metadata about the invoice
        
        return APIResponse(
            message="Invoice information retrieved successfully",
            data={
                "order_id": order_id,
                "invoice_available": True,
                "invoice_size": len(invoice_info["invoice"]) if invoice_info.get("invoice") else 0,
                "download_url": f"/api/orders/{order_id}/invoice/download"  # Would be actual download endpoint
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/delivery", response_model=APIResponse)
async def get_order_delivery_details(order_id: str) -> APIResponse:
    """Get delivery details for an order"""
    try:
        # Get order delivery info
        order_result = await db_service.get_order_by_id(order_id)
        
        if not order_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        order_data = order_result.get("data", [])
        
        if not order_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        order = order_data[0]
        
        delivery_details = {
            "order_id": order_id,
            "delivery_address": {
                "phone_number": order.get("phone_number"),
                "street_address": order.get("street_address"),
                "city": order.get("city"),
                "postal_code": order.get("postal_code"),
                "country": order.get("country")
            },
            "status": order["status"],
            "tracking_info": {
                "tracking_number": order.get("tracking_number"),
                "shipping_carrier": order.get("shipping_carrier"),
                "tracking_url": order.get("tracking_url")
            }
        }
        
        return APIResponse(
            message="Delivery details retrieved successfully",
            data=delivery_details
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations", response_model=APIResponse)
async def get_order_recommendations(
    limit: int = Query(10, description="Number of recommendations to return", ge=1, le=50)
) -> APIResponse:
    """Get recommended products based on order history (ML-based)"""
    try:
        # TODO: Integrate with ML service for real recommendations
        # For now, return placeholder response
        
        # This would typically:
        # 1. Analyze user's order history
        # 2. Call ML service for recommendations
        # 3. Return recommended products
        
        return APIResponse(
            message="Order-based recommendations retrieved successfully",
            data={
                "recommendations": [],
                "total": 0,
                "note": "ML integration pending - this endpoint will provide personalized product recommendations based on order history"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
