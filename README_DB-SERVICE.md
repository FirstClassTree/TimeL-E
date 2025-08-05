# cart is a dict matching the CartResponse model
```

#### Example Request (curl):

```bash
curl -X GET http://localhost:7000/carts/1234
```

### Update/Replace Cart ```PUT /carts/{user_id}```

Replaces the entire cart for a user (full upsert/replace operation).  
If a cart does not exist, creates a new one. Returns enriched product details and the latest `updated_at`.  

#### Request Body (JSON):

```json
{
  "user_id": 1234,
  "items": [
    {
      "product_id": 42,
      "quantity": 2
    }
  ]
}
```

#### Response:  
same format as "Get Cart" above, with `updated_at`.

#### Example Request (Backend usage):

```python
from ..models.base import Cart, CartItem

cart = Cart(
    user_id=1234,
    items=[
        CartItem(product_id=42, quantity=2),
    ]
)
result = await db_service.update_entity(
    "carts", 1234, cart.model_dump()
)
```

### Delete Cart ```DELETE /carts/{user_id}```
Deletes a user's cart.  
Returns HTTP 404 if the user or the cart do not exist.  

#### Response:

```json
{ "message": "Cart deleted successfully for user 1234" }
```

#### Example Request (Backend usage):

```python
await db_service.delete_entity("carts", user_id)
```

##########################################################

\# TODO:

add_cart_item(user_id, item) → POST /carts/{user_id}/items – add an item (or increment if exists)


update_cart_item(user_id, product_id, qty) → PUT /carts/{user_id}/items/{product_id} – set quantity for item (update/remove)


remove_cart_item(user_id, product_id) → DELETE /carts/{user_id}/items/{product_id} – remove item


clear_user_cart(user_id) → DELETE /carts/{user_id}} – clear cart


checkout_cart(user_id) → POST /carts/{user_id}/checkout – convert cart to order


### Create Cart ```POST /carts```

...

#### Request Body (JSON):

```json
```

#### Response:

```json
```

#### Example Request (Backend usage):

```python
```

### Create Cart ```POST /carts```

...

#### Request Body (JSON):

```json
```

#### Response:

```json
```

#### Example Request (Backend usage):

```python
```

### Full Example for Cart API (Backend usage):

```python
# Create a new cart for user
cart_data = {
    "user_id": 1234,
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 4, "quantity": 1}
    ]
}
resp = await db_service.create_entity(endpoint="/carts/", data=cart_data)

# Get cart
resp = await db_service.get_entity("carts", user_id)

# Update (replace) cart
cart_data["items"].append({"product_id": 7, "quantity": 3})
resp = await db_service.update_entity("carts", user_id, cart_data)

# Delete cart
await db_service.delete_entity("carts", user_id)
```

---

## Orders API

### Get Order Details ```GET /orders/{order_id}```

Get detailed order information with full tracking info, enriched products, and status history.

#### URL Parameters:
- `order_id` (required): Integer order ID

#### Response:

```json
{
  "success": true,
  "message": "Order 3422001 details retrieved successfully",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 5,
      "order_dow": 1,
      "order_hour_of_day": 14,
      "days_since_prior_order": 7,
      "total_items": 3,
      "total_price": 24.97,
      "status": "shipped",
      "delivery_name": "John Doe",
      "phone_number": "+1-555-1234",
      "street_address": "123 Main St",
      "city": "New York",
      "postal_code": "10001",
      "country": "US",
      "tracking_number": "1Z999AA1234567890",
      "shipping_carrier": "UPS",
      "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA1234567890",
      "invoice": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:45:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ],
      "status_history": [
        {
          "history_id": 1,
          "order_id": "3422001",
          "status": "pending",
          "changed_at": "2024-01-15T10:30:00Z",
          "changed_by": null,
          "note": "Order created"
        },
        {
          "history_id": 2,
          "order_id": "3422001",
          "status": "processing",
          "changed_at": "2024-01-15T12:00:00Z",
          "changed_by": "system",
          "note": "Order processing started"
        },
        {
          "history_id": 3,
          "order_id": "3422001",
          "status": "shipped",
          "changed_at": "2024-01-15T14:45:00Z",
          "changed_by": "fulfillment_center",
          "note": "Package shipped via UPS"
        }
      ]
    }
  ]
}
```

#### Error Responses:
- 400: "Invalid order ID format" (for non-integer order IDs)
- 404: "Order not found"
- 500: "Database error occurred"

#### Example Request (curl):

```bash
curl -X GET http://localhost:7000/orders/3422001
```

#### Example Request (Backend usage):

```python
# Get detailed order information
order_result = await db_service.get_entity("orders", "3422001")

if order_result.get("success"):
    order_data = order_result.get("data", [])[0]
    print(f"Order {order_data['order_id']} status: {order_data['status']}")
    print(f"Items: {len(order_data['items'])}")
    print(f"Status history: {len(order_data['status_history'])} changes")
```

### Get User Orders ```GET /orders/user/{user_id}```

Get paginated order history for a specific user with enriched item details.

#### URL Parameters:
- `user_id` (required): UUID4 user ID

#### Query Parameters:
- `limit` (optional): Number of orders to return (1-100, default: 20)
- `offset` (optional): Number of orders to skip (default: 0)

#### Response:

```json
{
  "success": true,
  "message": "Found 2 orders for user 550e8400-e29b-41d4-a716-446655440000",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 5,
      "total_items": 3,
      "total_price": 24.97,
      "status": "pending",
      "delivery_name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ]
    }
  ]
}
```

#### Example Request (curl):

```bash
curl -X GET "http://localhost:7000/orders/user/550e8400-e29b-41d4-a716-446655440000?limit=10&offset=0"
```

### Create Order ```POST /orders```

Create a new order with items. Orders are always created with "pending" status.

#### Request Body (JSON):

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "order_dow": 1,
  "order_hour_of_day": 14,
  "days_since_prior_order": 7,
  "delivery_name": "John Doe",
  "phone_number": "+1-555-1234",
  "street_address": "123 Main St",
  "city": "New York",
  "postal_code": "10001",
  "country": "US",
  "items": [
    {
      "product_id": 123,
      "quantity": 2,
      "add_to_cart_order": 1,
      "reordered": 0
    }
  ]
}
```

#### Response:

```json
{
  "success": true,
  "message": "Order created successfully",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 1,
      "status": "pending",
      "total_items": 1,
      "delivery_name": "John Doe",
      "phone_number": "+1-555-1234",
      "street_address": "123 Main St",
      "city": "New York",
      "postal_code": "10001",
      "country": "US",
      "created_at": "2025-01-05T17:30:00Z",
      "updated_at": "2025-01-05T17:30:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ]
    }
  ]
}
```

#### Example Request (Backend usage):

```python
# Create a new order
order_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "delivery_name": "John Doe",
    "phone_number": "+1-555-1234",
    "street_address": "123 Main St",
    "city": "New York",
    "postal_code": "10001",
    "country": "US",
    "items": [
        {
            "product_id": 123,
            "quantity": 2,
            "add_to_cart_order": 1,
            "reordered": 0
        }
    ]
}

order_result = await db_service.create_entity("orders", order_data)
```

### Key Features:

- Uses UUID4 for user references, integer IDs for orders
- Enriched Product Data: Full product details including descriptions, images, department/aisle info
- Status History: Complete chronological tracking of order status changes
- Tracking Integration: Support for tracking numbers, carriers, and URLs
- Invoice Support: Binary invoice data storage and retrieval
- Delivery Information: Complete shipping address and delivery name support
- Pagination: Efficient order-level pagination for user order history
