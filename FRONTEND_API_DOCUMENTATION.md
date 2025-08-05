# TimeL-E Frontend API Documentation

This document provides a comprehensive reference for all API endpoints available to the frontend.  
It details exactly what to send and what to expect in return for each API call.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [User Management](#user-management)
4. [Cart Operations](#cart-operations)
5. [Order Management](#order-management)
6. [Product Recommendations](#product-recommendations)
7. [Error Handling](#error-handling)
8. [Common Workflows](#common-workflows)

## API Overview

### Base URL

All API endpoints are prefixed with `/api`.

### Response Format

All API responses follow a consistent format:

```json
{
  "message": "Operation result message",
  "data": {
    // Response data specific to the endpoint
  }
}
```

### Data Format Conventions

- All request and response field names use **camelCase** for the frontend
- Dates and times are in ISO 8601 format (e.g., "2025-08-01T09:00:00Z")
- IDs are handled as follows:
  - User IDs: UUID4 strings (e.g., "550e8400-e29b-41d4-a716-446655440000")
  - Order IDs: Integers (sent as strings)
  - Cart IDs: Integers (sent as strings)
  - Product IDs: Integers

## Authentication

### Login

**Endpoint:** `POST /api/users/login`

**Purpose:** Authenticate users with email and password

**Request Body:**
```json
{
  "emailAddress": "john@example.com",  // Required
  "password": "userpassword"           // Required
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com",
    "phoneNumber": "+1-555-0123",              // Optional
    "streetAddress": "123 Main St",            // Optional
    "city": "Demo City",                       // Optional
    "postalCode": "12345",                     // Optional
    "country": "US",                           // Optional
    "daysBetweenOrderNotifications": 7,        // Optional
    "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",  // Optional
    "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",  // Optional
    "pendingOrderNotification": false,         // Optional
    "orderNotificationsViaEmail": true,        // Optional
    "lastNotificationSentAt": "2025-07-29T10:00:00Z",  // Optional
    "lastNotificationsViewedAt": "2025-08-01T09:15:00Z",  // Optional
    "lastLogin": "2025-08-01T08:30:00Z"        // Optional
  }
}
```

**Error Responses:**
- 401: "Invalid email or password"
- 500: "Login failed due to a server error"

### Demo Login (legacy)

**Endpoint:** `GET /api/users/login`

**Purpose:** Quick login for demo purposes

**Response (200 OK):**
```json
{
  "message": "Demo login successful", 
  "data": {
    "userId": "688",
    "firstName": "Demo",
    "lastName": "User 688",
    "emailAddress": "user688@timele-demo.com",
    "phoneNumber": "+1-555-0688",
    "streetAddress": "688 Demo Street",
    "city": "Demo City",
    "postalCode": "688",
    "country": "US",
    "demoUser": true,
    "mlPredictionsAvailable": true
  }
}
```

### Logout

**Endpoint:** `POST /api/users/logout`

**Purpose:** Logout endpoint (placeholder for future JWT implementation)

**Request:** No request body required

**Response (200 OK):**
```json
{
  "message": "Logout successful",
  "data": {
    "loggedOut": true
  }
}
```

## User Management

### Get User Profile

**Endpoint:** `GET /api/users/{userId}`

**Purpose:** Retrieve a user's profile information

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "User profile retrieved successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com",
    "phoneNumber": "+1-555-0123",              // Optional
    "streetAddress": "123 Main St",            // Optional
    "city": "Demo City",                       // Optional
    "postalCode": "12345",                     // Optional
    "country": "US",                           // Optional
    "daysBetweenOrderNotifications": 7,        // Optional
    "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",  // Optional
    "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",  // Optional
    "pendingOrderNotification": false,         // Optional
    "orderNotificationsViaEmail": true,        // Optional
    "lastNotificationSentAt": "2025-07-29T10:00:00Z",  // Optional
    "lastNotificationsViewedAt": "2025-08-01T09:15:00Z",  // Optional
    "lastLogin": "2025-08-01T08:30:00Z"        // Optional
  }
}
```

**Error Responses:**
- 404: "User {userId} not found"
- 422: "Invalid user ID format"
- 500: "Failed to retrieve user profile due to a server error"

### Register User

**Endpoint:** `POST /api/users/register`

**Purpose:** Register a new user

**Request Body:**
```json
{
  "firstName": "John",                         // Required
  "lastName": "Doe",                           // Required
  "email": "john@example.com",                 // Required (can use "email" or "emailAddress")
  "password": "securepassword",                // Required
  "phone": "+1-555-0123",                      // Optional (can use "phone" or "phoneNumber")
  "streetAddress": "123 Main St",              // Optional
  "city": "Demo City",                         // Optional
  "postalCode": "12345",                       // Optional
  "country": "US",                             // Optional
  "daysBetweenOrderNotifications": 7,          // Optional (default: 7)
  "orderNotificationsViaEmail": false,         // Optional (default: false)
  "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z"  // Optional (default: current time)
}
```

**Response (200 OK):**
```json
{
  "message": "User registered successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com",
    // ... other user fields
  }
}
```

**Error Responses:**
- 400: "Invalid registration data"
- 409: "Email address already exists"
- 500: "Registration failed due to a server error"

### Update User Profile

**Endpoint:** `PUT /api/users/{userId}`

**Purpose:** Update a user's profile information

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body (all fields optional):**
```json
{
  "firstName": "John",                         // Optional
  "lastName": "Smith",                         // Optional
  "email": "johnsmith@example.com",            // Optional (can use "email" or "emailAddress")
  "phone": "+1-555-0456",                      // Optional (can use "phone" or "phoneNumber")
  "streetAddress": "456 Oak St",               // Optional
  "city": "New City",                          // Optional
  "postalCode": "54321",                       // Optional
  "country": "US",                             // Optional
  "daysBetweenOrderNotifications": 14,         // Optional (must be between 1 and 365)
  "orderNotificationsViaEmail": true,          // Optional
  "orderNotificationsStartDateTime": "2025-08-01T09:00:00Z"  // Optional
}
```

**Response (200 OK):**
```json
{
  "message": "User profile updated successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "firstName": "John",
    "lastName": "Smith",
    "emailAddress": "johnsmith@example.com",
    // ... other updated fields
  }
}
```

**Error Responses:**
- 400: "No fields to update"
- 400: "Days between notifications must be between 1 and 365"
- 404: "User {userId} not found or no changes made"
- 409: "Email address already exists"
- 422: "Invalid user ID format"
- 500: "User update failed due to a server error"

### Delete User

**Endpoint:** `DELETE /api/users/{userId}`

**Purpose:** Delete a user account (requires password verification)

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:**
```json
{
  "password": "currentpassword"  // Required
}
```

**Response (200 OK):**
```json
{
  "message": "User deleted successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "deleted": true
  }
}
```

**Error Responses:**
- 400: "Current password is incorrect"
- 404: "User {userId} not found"
- 500: "Deletion failed due to a server error"

### Update Password

**Endpoint:** `PUT /api/users/{userId}/password`

**Purpose:** Update a user's password

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:**
```json
{
  "currentPassword": "oldpassword",  // Required
  "newPassword": "newpassword"       // Required
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "passwordUpdated": true
  }
}
```

**Error Responses:**
- 400: "Current password is incorrect"
- 404: "User {userId} not found"
- 500: "Password update failed due to a server error"

### Update Email

**Endpoint:** `PUT /api/users/{userId}/email`

**Purpose:** Update a user's email address with password verification

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:**
```json
{
  "currentPassword": "currentpassword",  // Required
  "newEmailAddress": "newemail@example.com"  // Required
}
```

**Response (200 OK):**
```json
{
  "message": "Email address updated successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "emailAddress": "newemail@example.com"
  }
}
```

**Error Responses:**
- 400: "Current password is incorrect"
- 404: "User {userId} not found"
- 409: "Email address already exists"
- 500: "Email update failed due to a server error"

### Get Notification Settings

**Endpoint:** `GET /api/users/{userId}/notification-settings`

**Purpose:** Retrieve a user's notification preferences

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "Notification settings retrieved successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "daysBetweenOrderNotifications": 7,        // Optional
    "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",  // Optional
    "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",  // Optional
    "pendingOrderNotification": false,         // Optional
    "orderNotificationsViaEmail": true,        // Optional
    "lastNotificationSentAt": "2025-07-29T10:00:00Z"  // Optional
  }
}
```

**Error Responses:**
- 404: "User {userId} not found"
- 500: "Failed to get notification settings due to a server error"

### Update Notification Settings

**Endpoint:** `PUT /api/users/{userId}/notification-settings`

**Purpose:** Update a user's notification preferences

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body (all fields optional):**
```json
{
  "daysBetweenOrderNotifications": 14,         // Optional (must be between 1 and 365)
  "orderNotificationsStartDateTime": "2025-08-01T09:00:00Z",  // Optional
  "orderNotificationsViaEmail": true           // Optional
}
```

**Response (200 OK):**
```json
{
  "message": "Notification settings updated successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "daysBetweenOrderNotifications": 14,
    "orderNotificationsStartDateTime": "2025-08-01T09:00:00Z",
    "orderNotificationsViaEmail": true,
    "orderNotificationsNextScheduledTime": "2025-08-15T09:00:00Z"
  }
}
```

**Error Responses:**
- 400: "No fields to update"
- 400: "Days between notifications must be between 1 and 365"
- 404: "User {userId} not found"
- 500: "Failed to update notification settings due to a server error"

### Get Order Status Notifications

**Endpoint:** `GET /api/users/{userId}/order-status-notifications`

**Purpose:** Retrieve list of user's notifications for updates in order statuses

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "Found 2 order status notifications for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "notifications": [
      {
        "orderId": 3422001,
        "status": "shipped",
        "changedAt": "2025-08-01T14:30:00Z"
      },
      {
        "orderId": 3422002,
        "status": "delivered",
        "changedAt": "2025-08-01T16:45:00Z"
      }
    ]
  }
}
```

**Error Responses:**
- 404: "User {userId} not found"
- 500: "Failed to get order status notifications due to a server error"

## Cart Operations

### Get Cart

**Endpoint:** `GET /api/cart/{userId}`

**Purpose:** Retrieve a user's shopping cart

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "Cart retrieved successfully for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      {
        "productId": 123,
        "quantity": 2,
        "addToCartOrder": 1,        // Optional
        "reordered": 0,             // Optional
        "productName": "Organic Milk",  // Optional
        "aisleName": "Dairy",       // Optional
        "departmentName": "Fresh Foods",  // Optional
        "description": "Fresh organic whole milk",  // Optional
        "price": 4.99,              // Optional
        "imageUrl": "https://example.com/images/milk.jpg"  // Optional
      }
    ],
    "totalItems": 1
  }
}
```

**Error Responses:**
- 404: "Cart not found for user {userId}"
- 422: "Invalid user ID format"
- 500: "Failed to retrieve cart due to a server error"

### Create Cart

**Endpoint:** `POST /api/cart`

**Purpose:** Create a new cart for a user

**Request Body:**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",  // Required
  "items": [                         // Optional
    {
      "productId": 123,              // Required
      "quantity": 2,                 // Optional (default: 1)
      "addToCartOrder": 1,           // Optional (default: 0)
      "reordered": 0                 // Optional (default: 0)
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "message": "Cart created successfully",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      {
        "productId": 123,
        "quantity": 2,
        "addToCartOrder": 1,
        "reordered": 0,
        "productName": "Organic Milk",
        "aisleName": "Dairy",
        "departmentName": "Fresh Foods",
        "description": "Fresh organic whole milk",
        "price": 4.99,
        "imageUrl": "https://example.com/images/milk.jpg"
      }
    ],
    "totalItems": 1
  }
}
```

**Error Responses:**
- 400: "One or more products not found"
- 409: "Cart already exists for user"
- 500: "Failed to create cart due to a server error"

### Update/Replace Cart

**Endpoint:** `PUT /api/cart/{userId}`

**Purpose:** Replace the entire cart for a user (full upsert/replace operation)

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:**
```json
{
  "items": [                         // Required
    {
      "productId": 123,              // Required
      "quantity": 2,                 // Optional (default: 1)
      "addToCartOrder": 1,           // Optional (default: 0)
      "reordered": 0                 // Optional (default: 0)
    },
    {
      "productId": 456,
      "quantity": 1
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Cart updated successfully",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      {
        "productId": 123,
        "quantity": 2,
        "addToCartOrder": 1,
        "reordered": 0,
        "productName": "Organic Milk",
        "aisleName": "Dairy",
        "departmentName": "Fresh Foods",
        "price": 4.99,
        "description": "Fresh organic whole milk",
        "imageUrl": "https://example.com/images/milk.jpg"
      },
      {
        "productId": 456,
        "quantity": 1,
        "addToCartOrder": 0,
        "reordered": 0,
        "productName": "Whole Wheat Bread",
        "aisleName": "Bakery",
        "departmentName": "Bakery",
        "price": 3.49,
        "description": "Freshly baked whole wheat bread",
        "imageUrl": "https://example.com/images/bread.jpg"
      }
    ],
    "totalItems": 2
  }
}
```

**Error Responses:**
- 400: "One or more products not found"
- 404: "Cart not found for user {userId}"
- 422: "Invalid user ID format"
- 500: "Failed to update cart due to a server error"

### Add Item to Cart

**Endpoint:** `POST /api/cart/{userId}/items`

**Purpose:** Add an item to the cart (or increment quantity if it exists)

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:**
```json
{
  "productId": 123,              // Required
  "quantity": 2,                 // Optional (default: 1)
  "addToCartOrder": 1,           // Optional (default: 0)
  "reordered": 0                 // Optional (default: 0)
}
```

**Response (200 OK):**
```json
{
  "message": "Item added to cart successfully",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      // Updated cart items with the new/updated item
    ],
    "totalItems": 2
  }
}
```

**Error Responses:**
- 400: "Product not found"
- 404: "Cart not found for user {userId}"
- 422: "Invalid user ID format"
- 500: "Failed to add item to cart due to a server error"

### Update Cart Item

**Endpoint:** `PUT /api/cart/{userId}/items/{productId}`

**Purpose:** Update the quantity of an item in the cart

**URL Parameters:**
- `userId` (required): UUID4 string
- `productId` (required): Integer product ID

**Request Body:**
```json
{
  "quantity": 3  // Required
}
```

**Response (200 OK):**
```json
{
  "message": "Cart item updated successfully",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      // Updated cart items with the updated quantity
    ],
    "totalItems": 2
  }
}
```

**Error Responses:**
- 404: "Cart item not found"
- 422: "Invalid user ID or product ID format"
- 500: "Failed to update cart item due to a server error"

### Remove Item from Cart

**Endpoint:** `DELETE /api/cart/{userId}/items/{productId}`

**Purpose:** Remove an item from the cart

**URL Parameters:**
- `userId` (required): UUID4 string
- `productId` (required): Integer product ID

**Response (200 OK):**
```json
{
  "message": "Item removed from cart successfully",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [
      // Remaining cart items after removal
    ],
    "totalItems": 1
  }
}
```

**Error Responses:**
- 404: "Cart item not found"
- 422: "Invalid user ID or product ID format"
- 500: "Failed to remove item from cart due to a server error"

### Delete Cart

**Endpoint:** `DELETE /api/cart/{userId}`

**Purpose:** Delete a user's entire cart

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "Cart deleted successfully for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "deleted": true
  }
}
```

**Error Responses:**
- 404: "Cart not found for user {userId}"
- 422: "Invalid user ID format"
- 500: "Failed to delete cart due to a server error"

### Clear Cart

**Endpoint:** `DELETE /api/cart/{userId}/clear`

**Purpose:** Clear all items from a user's cart without deleting the cart itself

**URL Parameters:**
- `userId` (required): UUID4 string

**Response (200 OK):**
```json
{
  "message": "Cart cleared successfully for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "cartId": "1",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "items": [],
    "totalItems": 0
  }
}
```

**Error Responses:**
- 404: "Cart not found"
- 422: "Invalid user ID format"
- 500: "Failed to clear cart due to a server error"

### Checkout Cart

**Endpoint:** `POST /api/cart/{userId}/checkout`

**Purpose:** Convert cart to an order

**URL Parameters:**
- `userId` (required): UUID4 string

**Request Body:** No request body required

**Response (200 OK):**
```json
{
  "message": "Checkout completed successfully for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "orderId": "3422001",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "orderNumber": 1,
    "status": "pending",
    "totalItems": 2,
    "totalPrice": 12.47,
    "createdAt": "2025-08-01T12:00:00Z",
    "updatedAt": "2025-08-01T12:00:00Z",
    "items": [
      // Order items with enriched product data
    ]
  }
}
```

**Error Responses:**
- 400: "Cart is empty"
- 404: "Cart not found for user {userId}"
- 422: "Invalid user ID format"
- 500: "Failed to checkout cart due to a server error"

## Order Management

### Get User Orders

**Endpoint:** `GET /api/orders/user/{userId}`

**Purpose:** Get paginated order history for a specific user

**URL Parameters:**
- `userId` (required): UUID4 string

**Query Parameters:**
- `limit` (optional): Number of orders to return (1-100, default: 20)
- `offset` (optional): Number of orders to skip (default: 0)

**Response (200 OK):**
```json
{
  "message": "Found 2 orders for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "orders": [
      {
        "orderId": "3422001",
        "userId": "550e8400-e29b-41d4-a716-446655440000",
        "orderNumber": 5,
        "totalItems": 3,
        "totalPrice": 24.97,
        "status": "pending",
        "deliveryName": "John Doe",           // Optional
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z",
        "items": [
          {
            "productId": 123,
            "productName": "Organic Milk",
            "quantity": 2,
            "addToCartOrder": 1,
            "reordered": 0,
            "price": 4.99,
            "description": "Fresh organic whole milk from grass-fed cows",
            "imageUrl": "https://example.com/images/organic-milk.jpg",
            "departmentName": "Dairy Eggs",
            "aisleName": "Milk"
          },
          // Additional items...
        ]
      },
      // Additional orders...
    ],
    "total": 2,
    "page": 1,
    "perPage": 20,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Error Responses:**
- 404: "User {userId} not found"
- 422: "Invalid user ID format"
- 500: "An internal server error occurred while retrieving orders for user {userId}"

### Get Order Details

**Endpoint:** `GET /api/orders/{orderId}`

**Purpose:** Get detailed order information with tracking, status history, and enriched products

**URL Parameters:**
- `orderId` (required): Order ID (integer as string)

**Response (200 OK):**
```json
{
  "message": "Order 3422001 details retrieved successfully",
  "data": {
    "orderId": "3422001",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "orderNumber": 5,
    "orderDow": 1,                            // Optional
    "orderHourOfDay": 14,                     // Optional
    "daysSincePriorOrder": 7,                 // Optional
    "totalItems": 3,
    "totalPrice": 24.97,
    "status": "shipped",
    "deliveryName": "John Doe",               // Optional
    "phoneNumber": "+1-555-1234",             // Optional
    "streetAddress": "123 Main St",           // Optional
    "city": "New York",                       // Optional
    "postalCode": "10001",                    // Optional
    "country": "US",                          // Optional
    "trackingNumber": "1Z999AA1234567890",    // Optional
    "shippingCarrier": "UPS",                 // Optional
    "trackingUrl": "https://www.ups.com/track?tracknum=1Z999AA1234567890",  // Optional
    "invoice": null,                          // Optional
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T14:45:00Z",
    "items": [
      {
        "productId": 123,
        "productName": "Organic Milk",
        "quantity": 2,
        "addToCartOrder": 1,
        "reordered": 0,
        "price": 4.99,
        "description": "Fresh organic whole milk from grass-fed cows",
        "imageUrl": "https://example.com/images/organic-milk.jpg",
        "departmentName": "Dairy Eggs",
        "aisleName": "Milk"
      }
    ],
    "statusHistory": [
      {
        "historyId": 1,
        "orderId": "3422001",
        "status": "pending",
        "changedAt": "2024-01-15T10:30:00Z",
        "changedBy": null,
        "note": "Order created"
      },
      {
        "historyId": 2,
        "orderId": "3422001",
        "status": "processing",
        "changedAt": "2024-01-15T12:00:00Z",
        "changedBy": "system",
        "note": "Order processing started"
      },
      {
        "historyId": 3,
        "orderId": "3422001",
        "status": "shipped",
        "changedAt": "2024-01-15T14:45:00Z",
        "changedBy": "fulfillment_center",
        "note": "Package shipped via UPS"
      }
    ]
  }
}
```

**Error Responses:**
- 400: "Invalid order ID format"
- 404: "Order {orderId} not found"
- 500: "An internal server error occurred while retrieving order {orderId}"

### Create Order

**Endpoint:** `POST /api/orders`

**Purpose:** Create a new order with items

**Request Body:**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",  // Required
  "orderDow": 1,                       // Optional (0=Sunday, 6=Saturday)
  "orderHourOfDay": 14,                // Optional (0-23)
  "daysSincePriorOrder": 7,            // Optional
  "totalItems": 2,                     // Optional (auto-calculated if not provided)
  "deliveryName": "John Doe",          // Optional
  "phoneNumber": "+1-555-1234",        // Optional
  "streetAddress": "123 Main St",      // Optional
  "city": "New York",                  // Optional
  "postalCode": "10001",               // Optional
  "country": "US",                     // Optional
  "items": [                           // Required (at least one item)
    {
      "productId": 123,                // Required
      "quantity": 2,                   // Optional (default: 1)
      "addToCartOrder": 1,             // Optional (default: 0)
      "reordered": 0                   // Optional (default: 0)
    },
    {
      "productId": 456,
      "quantity": 1
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Order created successfully",
  "data": {
    "orderId": "3422001",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "orderNumber": 1,
    "status": "pending",
    "totalItems": 2,
    "totalPrice": 12.47,
    "deliveryName": "John Doe",
    "createdAt": "2025-08-01T12:00:00Z",
    "updatedAt": "2025-08-01T12:00:00Z",
    "items": [
      {
        "productId": 123,
        "productName": "Organic Milk",
        "quantity": 2,
        "price": 4.99,
        "description": "Fresh organic whole milk",
        "imageUrl": "https://example.com/images/milk.jpg"
      },
      {
        "productId": 456,
        "productName": "Whole Wheat Bread",
        "quantity": 1,
        "price": 3.49,
        "description": "Freshly baked whole wheat bread",
        "imageUrl": "https://example.com/images/bread.jpg"
      }
    ]
  }
}
```

**Error Responses:**
- 400: "Order must contain at least one item"
- 400: "User {userId} not found"
- 400: "Product {productId} not found"
- 500: "Failed to create order"

## Product Recommendations

### Get ML Predictions

**Endpoint:** `GET /api/predictions/user/{userId}`

**Purpose:** Get personalized product recommendations for a user

**URL Parameters:**
- `userId` (required): UUID4 string

**Query Parameters:**
- None

**Response (200 OK):**
```json
{
  "message": "Generated 2 ML predictions for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "predictions": [
      {
        "productId": 789,
        "productName": "Greek Yogurt",
        "score": 0.8
      },
      {
        "productId": 234,
        "productName": "Bananas",
        "score": 0.8
      }
    ],
    "total": 2
  }
}
```

**Response (200 OK - No Predictions):**
```json
{
  "message": "No predictions available for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "predictions": [],
    "total": 0
  }
}
```

**Error Responses:**
- 500: "Failed to get predictions for user {userId}: [error details]"

## Error Handling

### Error Response Format

API errors are returned as FastAPI HTTPException responses with the following structure:

```json
{
  "detail": "Specific error message"
}
```

**Note:** Successful responses use the `APIResponse` format with `message` and `data` fields, but error responses use FastAPI's standard `detail` field.

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data or missing required fields
- **401 Unauthorized**: Authentication failed
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists (e.g., email already registered)
- **422 Unprocessable Entity**: Invalid data format (e.g., invalid UUID format)
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: External service temporarily unavailable

### Common Error Scenarios

#### User ID Validation
- **Invalid Format**: "Invalid user ID format" (422)
- **Not Found**: "User {userId} not found" (404)

#### Authentication Errors
- **Invalid Credentials**: "Invalid email or password" (401)
- **Password Verification**: "Current password is incorrect" (400)

#### Data Validation Errors
- **Missing Fields**: "No fields to update" (400)
- **Invalid Range**: "Days between notifications must be between 1 and 365" (400)
- **Duplicate Data**: "Email address already exists" (409)

#### Resource Errors
- **Not Found**: "Cart not found for user {userId}" (404)
- **Empty Cart**: "Cart is empty" (400)
- **Product Not Found**: "Product {productId} not found" (400)

#### Service Errors
- **Database Issues**: "Service temporarily unavailable" (503)
- **ML Service**: "ML service temporarily unavailable" (503)
- **Generic Server**: "Operation failed due to a server error" (500)

## Common Workflows

### User Registration and Login Flow

1. **Register New User**
   ```
   POST /api/users/register
   → Returns user profile with userId
   ```

2. **Login User**
   ```
   POST /api/users/login
   → Returns complete user profile
   ```

3. **Update Profile** (Optional)
   ```
   PUT /api/users/{userId}
   → Returns updated profile
   ```

### Shopping Cart Workflow

1. **Get User's Cart**
   ```
   GET /api/cart/{userId}
   → Returns cart with items (or empty cart)
   ```

2. **Add Items to Cart**
   ```
   POST /api/cart/{userId}/items
   → Returns updated cart
   ```

3. **Update Item Quantities**
   ```
   PUT /api/cart/{userId}/items/{productId}
   → Returns updated cart
   ```

4. **Checkout Cart**
   ```
   POST /api/cart/{userId}/checkout
   → Returns new order details
   ```

### Order Management Workflow

1. **View Order History**
   ```
   GET /api/orders/user/{userId}?limit=10&offset=0
   → Returns paginated order list
   ```

2. **Get Order Details**
   ```
   GET /api/orders/{orderId}
   → Returns detailed order with status history
   ```

3. **Check Order Status Notifications**
   ```
   GET /api/users/{userId}/order-status-notifications
   → Returns recent status changes
   ```

### Product Recommendation Workflow

1. **Get Personalized Recommendations**
   ```
   GET /api/predictions/user/{userId}
   → Returns ML-powered product suggestions
   ```

2. **Add Recommended Items to Cart**
   ```
   POST /api/cart/{userId}/items
   → Add recommended products to cart
   ```

### Notification Management Workflow

1. **Get Current Settings**
   ```
   GET /api/users/{userId}/notification-settings
   → Returns notification preferences
   ```

2. **Update Notification Preferences**
   ```
   PUT /api/users/{userId}/notification-settings
   → Returns updated settings
   ```

3. **Check for New Notifications**
   ```
   GET /api/users/{userId}/order-status-notifications
   → Returns unread status updates
   ```

### Demo User Workflow

For development and testing purposes:

1. **Quick Demo Login**
   ```
   GET /api/users/login
   → Returns random demo user with ML predictions enabled
   ```

2. **Use Demo User ID**
   ```
   Use returned userId for all subsequent API calls
   ```

## Implementation Notes

### Field Name Conversion
- The API automatically converts between camelCase (frontend) and snake_case (backend)
- Always use camelCase in your frontend requests and expect camelCase in responses
- Examples: `firstName` ↔ `first_name`, `userId` ↔ `user_id`, `orderDow` ↔ `order_dow`

### UUID Handling
- User IDs are UUID4 strings: `"550e8400-e29b-41d4-a716-446655440000"`
- Order IDs and Cart IDs are integers sent as strings: `"3422001"`
- Product IDs are integers: `123`

### Date/Time Format
- All timestamps use ISO 8601 format: `"2025-08-01T12:00:00Z"`
- Times are in UTC timezone
- Frontend should convert to local timezone for display

### Pagination
- Use `limit` and `offset` parameters for paginated endpoints
- Check `hasNext` and `hasPrev` flags in responses
- Default limits are typically 10-20 items per page

### Error Handling Best Practices
- Always check the HTTP status code first
- Parse the `detail` field for error descriptions (note: these are often general messages, not very user-friendly)
- Implement client-side error message mapping for better user experience
- Handle common scenarios like network timeouts and service unavailability
- Implement retry logic for 503 (Service Unavailable) errors
- Consider creating user-friendly error messages based on status codes rather than relying on `detail` text

### Performance Considerations
- Cart and order responses include enriched product data to minimize API calls
- Use pagination for large datasets (order history, product catalogs)
- ML predictions are cached and updated periodically
- Client-side caching is already implemented using Zustand with persistence:
  - User profiles and authentication state are persisted in localStorage
  - Cart state is cached in memory with optimistic updates for better UX
  - Demo authentication tokens are stored locally (actual JWT implementation pending)

This documentation provides a complete reference for integrating with the TimeL-E API.  
All endpoints use consistent patterns for requests, responses, and error handling to ensure a smooth development experience.
