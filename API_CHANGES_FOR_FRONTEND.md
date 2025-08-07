# API Changes for Frontend Developers

## BREAKING CHANGE: Complete camelCase Support for Frontend (see below)

The backend now provides **complete camelCase support** for all frontend-facing endpoints.  
All request and response field names are now consistently camelCase for the frontend, while maintaining snake_case internally.

## Dual-ID Architecture Implementation (Users Only)

**The db_service and backend have implemented a dual-ID architecture for users only, providing optimal performance and security:**

- **Users**: Dual-ID architecture with internal numeric IDs and external UUID4 strings
  - **Internal IDs**: Numeric primary keys used internally for database operations and foreign key relationships
  - **External IDs**: UUID4 strings exposed to the frontend via API endpoints as `userId`
  - **Security Enhancement**: Prevents exposure of sequential integer IDs in URLs, eliminating enumeration attacks
  - **URL Parameters**: User endpoints use `{user_id}` (UUID4 string)
  - **Response Fields**: All API responses return `userId` as UUID4 strings

- **Orders & Carts**: Simple integer IDs (no dual-ID architecture)
  - **Single IDs**: BIGINT serial primary keys used both internally and externally
  - **URL Parameters**: Order endpoints use `{order_id}` (integer), Cart endpoints use `{user_id}` (UUID4 for user reference)
  - **Response Fields**: `orderId` and `cartId` are integers (sent as strings to frontend)
  - **Starting Points**: Orders start at 3,422,000+, Carts start at 1+ (preserving CSV data)

**Key Notes:**
- User endpoints: `/api/users/{user_id}` (UUID4 string)
- Order endpoint: `/api/orders/{order_id}` (integer as string)
- Cart endpoints: `/api/cart/{user_id}` (UUID4 string for user reference)
- User `userId` fields are UUID4 strings
- Order `orderId` and Cart `cartId` fields are integers (sent as strings)


## Overview
This document details all API changes made to the backend endpoints including:
- Major user management system overhaul with security enhancements and notification features
- Complete camelCase standardization for frontend communication
- Users, cart, orders, and product endpoint camelCase support

**Note**: The `/api` prefix remains unchanged from the frontend perspective.  
All endpoints continue to use their existing URL patterns.

---

## CHANGED ENDPOINTS

### 1. **GET `/api/users/{user_id}` - User Profile Response Enhanced**

**Response Changes:**
- **ADDED**: Notification-related fields in user profile response
- **CHANGED**: User name structure (single `name` → `first_name` + `last_name`)

**OLD Response:**
```json
{
  "message": "User profile retrieved successfully",
  "data": {
    "user_id": "123",
    "name": "John Doe",
    "email_address": "john@example.com",
    "phone_number": "+1-555-0123",
    "street_address": "123 Main St",
    "city": "Demo City",
    "postal_code": "12345",
    "country": "US"
  }
}
```

**NEW Response:**

```json
{
   "message": "User profile retrieved successfully",
   "data": {
      "userId": "123",
      "firstName": "John",
      "lastName": "Doe",
      "emailAddress": "john@example.com",
      "phoneNumber": "+1-555-0123",
      "streetAddress": "123 Main St",
      "city": "Demo City",
      "postalCode": "12345",
      "country": "US",
      "daysBetweenOrderNotifications": 7,
      "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",
      "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",
      "pendingOrderNotification": false,
      "orderNotificationsViaEmail": true,
      "lastNotificationSentAt": "2025-07-29T10:00:00Z",
      "lastLogin": "2025-08-01T08:30:00Z",
      "lastNotificationsViewedAt": "2025-08-01T09:15:00Z",
      "hasActiveCart": true
   }
}
```

### 2. **POST `/api/users/register` - Registration Request Enhanced**

**Request Changes:**
- **CHANGED**: User name structure (`name` → `firstName` + `lastName` with aliases)
- **ADDED**: Notification settings fields
- **CHANGED**: Email field accepts both `email` and `email_address`
- **CHANGED**: Phone field accepts `phone` alias

**OLD Request:**
```json
{
  "name": "John Doe",
  "email_address": "john@example.com",
  "password": "securepassword",
  "phone_number": "+1-555-0123",
  "street_address": "123 Main St",
  "city": "Demo City",
  "postal_code": "12345",
  "country": "US"
}
```

**NEW Request (camelCase aliases):**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "emailAddress": "john@example.com",
  "password": "securepassword",
  "phoneNumber": "+1-555-0123",
  "streetAddress": "123 Main St",
  "city": "Demo City",
  "postalCode": "12345",
  "country": "US",
  "daysBetweenOrderNotifications": 7,
  "orderNotificationsViaEmail": false,
  "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z"
}
```

**Minimal Request (required fields only):**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "emailAddress": "john@example.com",
  "password": "securepassword"
}
```

**Field Requirements:**
- **Required**: `firstName`, `lastName`, `email`, `password`
- **Optional**: All other fields including notification settings
- **Datetime Format**: ISO 8601 format (e.g., "2025-07-30T10:00:00Z")

**Response Changes:**
- **CHANGED**: Returns full UserResponse model instead of limited fields
- **ADDED**: All notification fields in response

### 3. **PUT `/api/users/{user_id}` - Profile Update Enhanced**

**Request Changes:**
- **CHANGED**: Name fields (`name` → `firstName`/`lastName` with aliases)
- **NOTE**: Notification fields are supported in this endpoint as well as in the standalone notifications endpoint

**OLD Request:**
```json
{
  "name": "John Smith",
  "email_address": "johnsmith@example.com",
  "phone_number": "+1-555-0456",
   "street_address": "123 Main St",
  "city": "Demo City",
  "postal_code": "12345",
  "country": "US"
}
```

**NEW Request (camelCase aliases):**
```json
{
  "firstName": "John",
  "lastName": "Smith", 
  "emailAddress": "johnsmith@example.com",
  "phoneNumber": "+1-555-0456"
}
```

**Minimal Request:**
```json
{
  "firstName": "John"
}
```

**Field Requirements:**
- **All fields optional** (partial updates supported)
- **Available fields**: `firstName`, `lastName`, `email`, `phone`,  
- `street_address`, `city`, `postal_code`, `country`, `days_between_order_notifications`,  
- `order_notifications_via_email`, `order_notifications_start_date_time` 

**Response (Success - 200):**
```json
{
  "message": "User profile updated successfully",
  "data": {
    "userId": "123",
    "firstName": "John",
    "lastName": "Smith",
    "emailAddress": "johnsmith@example.com",
    "phoneNumber": "+1-555-0456",
    "streetAddress": "123 Main St",
    "city": "Demo City",
    "postalCode": "12345",
    "country": "US",
    "daysBetweenOrderNotifications": 7,
    "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",
    "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",
    "pendingOrderNotification": false,
    "orderNotificationsViaEmail": true,
    "lastNotificationSentAt": "2025-07-29T10:00:00Z"
  }
}
```

**Error Responses:**
- **400**: "No fields to update" (if empty request)
- **404**: "User {user_id} not found or no changes made"
- **409**: "Email address already exists" (if email conflicts)
- **422**: "Invalid user ID format"
- **500**: "User update failed due to a server error"

### 4. **DELETE `/api/users/{user_id}` - Now Requires Password Verification**

**MAJOR SECURITY CHANGE**: Delete now requires password verification in request body.

**OLD Request:**
```
DELETE /api/users/123
(No request body required)
```

**NEW Request:**
```json
DELETE /api/users/123
Content-Type: application/json

{
  "password": "currentpassword"
}
```

**Error Responses Enhanced:**
- **400**: "Current password is incorrect" (if password verification fails)
- **404**: "User {user_id} not found"
- **500**: "Deletion failed due to a server error"

### 5. **PUT `/api/users/{user_id}/password` - Enhanced Security**

**Request Unchanged** but **Error Handling Enhanced:**
- **400**: "Current password is incorrect"
- **404**: "User {user_id} not found" 
- **500**: "Password update failed due to a server error"

**Response Unchanged:**
```json
{
  "message": "Password updated successfully",
  "data": {
    "userId": "123",
    "passwordUpdated": true
  }
}
```

### 6. **GET `/api/users/login` - Demo Login Response Enhanced**

**Response Changes:**
- **CHANGED**: Name structure in demo response

**OLD Response:**
```json
{
  "message": "Demo login successful",
  "data": {
    "user_id": "688",
    "name": "Demo User 688",
    "email_address": "user688@timele-demo.com",
    // ... other fields
  }
}
```

**NEW Response:**
```json
{
  "message": "Demo login successful", 
  "data": {
    "userId": "688",
    "firstName": "Demo",
    "lastName": "User 688",
    "emailAddress": "user688@timele-demo.com",
    // ... other fields
  }
}
```

---

## NEW ENDPOINTS

### 1. **POST `/api/users/login` - Real Authentication**

**Purpose**: Authenticate users with email and password (not just demo)  
Returns full user information, including `lastLogin` and `lastNotificationsViewedAt` (ISO strings), and `hasActiveCart` (bool).

**Request:**
```json
{
  "emailAddress": "john@example.com",
  "password": "userpassword"
}
```

**Response (Success - 200):**
```json
{
  "message": "Login successful",
  "data": {
    "userId": "123",
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com",
    "phoneNumber": "+1-555-0123",
    // ... full user profile with notification fields and timestamps
  }
}
```

**Error Responses:**
- **401**: "Invalid email or password"
- **500**: "Login failed due to a server error"

### 2. **GET `/api/users/{user_id}/notification-settings` - Get Notification Settings**

**Purpose**: Retrieve user's notification preferences

**Request:**
```
GET /api/users/123/notification-settings
```

**Response (Success - 200):**
```json
{
  "message": "Notification settings retrieved successfully",
  "data": {
    "userId": "999",
    "daysBetweenOrderNotifications": 7,
    "orderNotificationsStartDateTime": "2025-07-30T10:00:00Z",
    "orderNotificationsNextScheduledTime": "2025-08-06T10:00:00Z",
    "pendingOrderNotification": false,
    "orderNotificationsViaEmail": true,
    "lastNotificationSentAt": "2025-07-29T10:00:00Z"
  }
}
```

**Error Responses:**
- **404**: "User {user_id} not found"
- **500**: "Failed to get notification settings due to a server error"

### 3. **PUT `/api/users/{user_id}/notification-settings` - Update Notification Settings**

**Purpose**: Update user's notification preferences. Supports partial updates.  

**Request:**
```json
{
  "daysBetweenOrderNotifications": 14,
  "orderNotificationsStartDateTime": "2025-08-01T09:00:00Z",
  "orderNotificationsViaEmail": true
}
```

**Validation:**
- `days_between_order_notifications`: Must be between 1 and 365
- All fields are optional (partial updates supported)
- **Datetime Format**: Send in ISO 8601 format (e.g., "2025-08-01T09:00:00Z")

**Note**: Backend expects datetime in ISO 8601 format and returns datetime in the same format.

**Response (Success - 200):**
```json
{
  "message": "Notification settings updated successfully",
  "data": {
    "userId": "999",
    "daysBetweenOrderNotifications": 14,
    "orderNotificationsStartDateTime": "2025-08-01T09:00:00Z",
    "orderNotificationsViaEmail": true,
    "orderNotificationsNextScheduledTime": "2025-08-15T09:00:00Z"
  }
}
```

**Error Responses:**
- **400**: "No fields to update" (if empty request)
- **404**: "User {user_id} not found"
- **422**: Validation errors for invalid field values
- **500**: "Failed to update notification settings due to a server error"

### 4. **PUT `/api/users/{user_id}/email` - Update Email with Password Verification**

**Purpose**: Update user's email address with password verification for security

**Request:**
```json
{
  "currentPassword": "currentpassword",
  "newEmailAddress": "newemail@example.com"
}
```

**Response (Success - 200):**
```json
{
  "message": "Email address updated successfully",
  "data": {
    "userId": "123",
    "emailAddress": "newemail@example.com"
  }
}
```

**Error Responses:**
- **400**: "Current password is incorrect"
- **404**: "User {user_id} not found"
- **409**: "Email address already exists"
- **500**: "Email update failed due to a server error"

### 5. **POST `/api/users/logout` - Logout Endpoint**

**Purpose**: Logout endpoint (placeholder for future JWT implementation)

**Request:**
```
POST /api/users/logout
(No request body required)
```

**Response (Success - 200):**
```json
{
  "message": "Logout successful",
  "data": {
    "loggedOut": true
  }
}
```

### 6. **GET `/api/users/{user_id}/order-status-notifications` - Get Order Status Notifications**

**Purpose**: Retrieve list of user's notifications for updates in order statuses.  

**Request:**
```
GET /api/users/{user_id}/order-status-notifications
```

**Response (Success - 200):**
```json
{
  "message": "Found 2 order status notifications for user 123",
  "data": {
    "notifications": [
      {
        "orderId": 456,
        "status": "shipped",
        "changedAt": "2025-08-01T14:30:00Z"
      },
      {
        "orderId": 789,
        "status": "delivered",
        "changedAt": "2025-08-01T16:45:00Z"
      }
    ]
  }
}
```

**Error Responses:**
- **404**: "User {user_id} not found"
- **500**: "Failed to get order status notifications due to a server error"
---

## ENHANCED ERROR HANDLING

### Centralized Error System
The new version implements centralized error handling system with:

**Key New Error Responses** (in addition to existing ones):
- **422**: "Invalid user ID format" (for malformed user IDs)
- **400**: "Current password is incorrect" (for password verification failures)
- **400**: "Days between notifications must be between 1 and 365" (for notification validation)
- **401**: "Invalid email or password" (for authentication failures)
- **503**: "Service temporarily unavailable" (for database connection issues)

**Enhanced Error Detection:**
- Automatic parsing error detection (invalid user ID formats)
- Database constraint violation detection
- Service communication error handling
- Initial move towards comprehensive logging for debugging
- Sanitized error messages (no sensitive data leakage)

**Note**: The above are key new/enhanced error responses.  
Standard HTTP errors (404, 409, 500, etc.) continue to work as before.

---

## MIGRATION CHECKLIST FOR FRONTEND DEVELOPERS

### Immediate Changes Required:

1. **Update User Registration**:
   - Change `name` field to `firstName` and `lastName`
   - Can use `email` instead of `email_address`
   - Can use `phone` instead of `phone_number`
   - Add optional notification settings fields

3. **Update User Profile Handling**:
   - Expect `first_name`/`last_name` instead of `name`
   - Handle new notification fields in user profile responses

4. **Update Delete User Flow**:
   - **CRITICAL**: Add password confirmation dialog
   - Send password in request body for DELETE requests
   - Handle new error responses

5. **Add New Features**:
   - Implement notification settings management UI
   - Add email update with password verification
   - Implement real login flow (POST `/users/login`)
   - Add logout functionality

### Optional Enhancements:

1. **Enhanced Error Handling**: Update error handling to use the new standardized error messages
2. **Notification Management**: Build UI for notification preferences
3. **Security Features**: Implement password verification flows for sensitive operations

---

## BREAKING CHANGES SUMMARY

1. **User model structure**: `name` → `first_name` + `last_name`
2. **Delete user security**: Now requires password verification
3. **Response format**: User profiles now include notification fields
4. **Registration fields**: Name structure changed, notification fields added
5. **User profile update fields**: Name structure changed, notification fields added

---

## SUPPORT

For questions about these API changes, refer to:
- Backend router: `backend/app/routers/users.py`
- Database service: `db_service/app/users_routers.py`
- User models: `db_service/app/db_core/models/users.py`



## CAMELCASE STANDARDIZATION

### All Frontend-Facing Endpoints Now Support camelCase  

The following endpoints now automatically convert between camelCase (frontend) and snake_case (backend):

#### **Cart Endpoints (`/api/cart/*`)**
- **Request Fields**: `productId`, `quantity` (instead of `product_id`)
- **Response Fields**: `userId`, `cartId`, `totalItems`, `totalQuantity`, `productId`, `productName`, `aisleName`, `departmentName`
- **URL Parameters**: Uses `{user_id}` (UUID4 string for user reference)
- **ID Types**: `userId` is UUID4 string, `cartId` is integer (sent as string)

**Example Cart Request:**
```json
{
  "productId": 123,
  "quantity": 2
}
```

**Example Cart Response:**
```json
{
  "success": true,
  "data": {
    "userId": "456",
    "cartId": "1",
    "items": [
      {
        "productId": 123,
        "quantity": 2,
        "productName": "Organic Milk",
        "aisleName": "Dairy",
        "departmentName": "Fresh Foods"
      }
    ],
    "totalItems": 1,
    "totalQuantity": 2
  }
}
```

---

## **Order Endpoints (`/api/orders/*`)**

### 1. **GET `/api/orders/user/{user_id}`**

- **Request Fields**: `userId`, `productId`, `quantity`, `addToCartOrder`, `reordered`, `orderDow`, `orderHourOfDay`, `daysSincePriorOrder`, `totalItems`, `phoneNumber`, `streetAddress`, `city`, `postalCode`, `country`, `trackingNumber`, `shippingCarrier`, `trackingUrl`
- **Response Fields**: `orderId`, `userId`, `orderNumber`, `totalItems`, `totalPrice`, `status`, `phoneNumber`, `streetAddress`, `city`, `postalCode`, `country`, `trackingNumber`, `shippingCarrier`, `trackingUrl`, `createdAt`, `updatedAt`, `productId`, `productName`, `quantity`, `addToCartOrder`, `reordered`, `price`, `description`, `imageUrl`, `departmentName`, `aisleName`
- **URL Parameters**: Uses `{user_id}` (UUID4 string for user orders)
- **ID Types**: `userId` is UUID4 string, `orderId` is integer (sent as string)
- **Status**: Order status is always "pending" for new orders and cannot be set by clients
- **Enhanced Features**: 
  - **Proper Pagination**: `GET /orders/user/{user_id}` now uses correct order-level pagination
  - **Enriched Product Data**: Order items include full product details (name, price, description, image, department, aisle)
  - **Complete Order Metadata**: Responses include `totalPrice`, `createdAt`, `updatedAt` timestamps
  - **UUID4 Compatibility**: Handles UUID4 user IDs with internal conversion


**Old Response Format**

```json
{
  "success": true,
  "message": "Found 2 orders for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "orders": [
      {
        "order_id": "3422001",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "order_number": 5,
        "status": "pending",
        "total_items": 3,
        "total_price": null,
        "created_at": null,
        "updated_at": null,
        "items": [
          {
            "product_id": 123,
            "product_name": "Organic Milk",
            "quantity": 2
          },
          {
            "product_id": 456,
            "product_name": "Whole Wheat Bread",
            "quantity": 1
          }
        ]
      },
      {
        "order_id": "3422002",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "order_number": 4,
        "status": "shipped",
        "total_items": 1,
        "total_price": null,
        "created_at": null,
        "updated_at": null,
        "items": [
          {
            "product_id": 789,
            "product_name": "Cheddar Cheese",
            "quantity": 1
          }
        ]
      }
    ],
    "total": 2,
    "page": 1,
    "per_page": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

**New Response Format**

```json
{
  "success": true,
  "message": "Found 2 orders for user 550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "orders": [
      {
        "order_id": "3422001",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "order_number": 5,
        "total_items": 3,
        "total_price": 24.97,
        "status": "pending",
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
          },
          {
            "product_id": 456,
            "product_name": "Whole Wheat Bread",
            "quantity": 1,
            "add_to_cart_order": 2,
            "reordered": 0,
            "price": 3.49,
            "description": "Freshly baked whole wheat bread with seeds",
            "image_url": "https://example.com/images/wheat-bread.jpg",
            "department_name": "Bakery",
            "aisle_name": "Packaged Bread"
          },
          {
            "product_id": 789,
            "product_name": "Organic Bananas",
            "quantity": 1,
            "add_to_cart_order": 3,
            "reordered": 1,
            "price": 2.99,
            "description": "Sweet organic bananas, perfect for snacking",
            "image_url": "https://example.com/images/bananas.jpg",
            "department_name": "Produce",
            "aisle_name": "Fresh Fruits"
          }
        ]
      },
      {
        "order_id": "3422002",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "order_number": 4,
        "total_items": 2,
        "total_price": 18.47,
        "status": "shipped",
        "created_at": "2024-01-14T14:22:00Z",
        "updated_at": "2024-01-14T16:45:00Z",
        "items": [
          {
            "product_id": 321,
            "product_name": "Cheddar Cheese",
            "quantity": 1,
            "add_to_cart_order": 1,
            "reordered": 0,
            "price": 6.99,
            "description": "Sharp aged cheddar cheese block",
            "image_url": "https://example.com/images/cheddar.jpg",
            "department_name": "Dairy Eggs",
            "aisle_name": "Cheese"
          },
          {
            "product_id": 654,
            "product_name": "Greek Yogurt",
            "quantity": 2,
            "add_to_cart_order": 2,
            "reordered": 0,
            "price": 5.74,
            "description": "Creamy Greek yogurt with live cultures",
            "image_url": "https://example.com/images/greek-yogurt.jpg",
            "department_name": "Dairy Eggs",
            "aisle_name": "Yogurt"
          }
        ]
      }
    ],
    "total": 2,
    "page": 1,
    "per_page": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

### 2. **GET `/api/orders/{order_id}`** - Get Order Details

**NEW ENDPOINT**: Get detailed order information with shipping address, full tracking info, enriched products, and status history.

**Request:**
```
GET /api/orders/3422001
```

**Response (Success - 200):**
```json
{
  "message": "Order 3422001 details retrieved successfully",
  "data": {
    "orderId": "3422001",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "orderNumber": 5,
    "orderDow": 1,
    "orderHourOfDay": 14,
    "daysSincePriorOrder": 7,
    "totalItems": 3,
    "totalPrice": 24.97,
    "status": "shipped",
    "deliveryName": "John Doe",
    "phoneNumber": "+1-555-1234",
    "streetAddress": "123 Main St",
    "city": "New York",
    "postalCode": "10001",
    "country": "US",
    "trackingNumber": "1Z999AA1234567890",
    "shippingCarrier": "UPS",
    "trackingUrl": "https://www.ups.com/track?tracknum=1Z999AA1234567890",
    "invoice": null,
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

**Key Features:**
- **Complete Order Information**: All order metadata including tracking details
- **Enriched Product Data**: Full product details with descriptions, images, department/aisle info
- **Status History**: Chronological order status changes with timestamps and notes
- **Invoice Support**: Returns invoice binary data if available (null in example)
- **Tracking Integration**: Direct tracking URLs for supported carriers

**Error Responses:**
- **400**: "Invalid order ID format" (for non-integer order IDs)
- **404**: "Order {order_id} not found"
- **500**: "An internal server error occurred while retrieving order {order_id}"

### 3. **POST `/api/orders/`** - Create order

## Complete Order Creation Data Flow

### **Frontend → Backend:**
Frontend sends camelCase (automatically converted to snake_case by backend):
```json
{
  "userId": "uuid4-string",
  "items": [
    {
      "productId": 123,
      "quantity": 2,
      "addToCartOrder": 1,
      "reordered": 0
    }
  ],
  "deliveryName": "John Doe",
  "phoneNumber": "+1-555-1234",
  "streetAddress": "123 Main St",
  "city": "New York",
  "postalCode": "10001",
  "country": "US"
}
```

### **Backend → db_service:**
Backend sends complete snake_case data with all optional fields:
```json
{
  "user_id": "uuid4-string",
  "order_dow": null,
  "order_hour_of_day": null,
  "days_since_prior_order": null,
  "total_items": 1,
  "phone_number": "+1-555-1234",
  "street_address": "123 Main St",
  "city": "New York",
  "postal_code": "10001",
  "country": "US",
  "tracking_number": null,
  "shipping_carrier": null,
  "tracking_url": null,
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

### **db_service → Backend:**
db_service returns ServiceResponse with complete order data:
```json
{
  "success": true,
  "message": "Order created successfully",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "uuid4-string",
      "order_number": 1,
      "status": "pending",
      "total_items": 1,
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
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0
        }
      ]
    }
  ]
}
```

### **Backend → Frontend:**
Backend extracts data and returns APIResponse (automatically converted to camelCase):
```json
{
  "message": "Order created successfully",
  "data": [
    {
      "orderId": "3422001",
      "userId": "uuid4-string",
      "orderNumber": 1,
      "status": "pending",
      "totalItems": 1,
      "phoneNumber": "+1-555-1234",
      "streetAddress": "123 Main St",
      "city": "New York",
      "postalCode": "10001",
      "country": "US",
      "createdAt": "2025-01-05T17:30:00Z",
      "updatedAt": "2025-01-05T17:30:00Z",
      "items": [
        {
          "productId": 123,
          "quantity": 2,
          "addToCartOrder": 1,
          "reordered": 0
        }
      ]
    }
  ]
}
```

**Key Features:**
- **Alignment**: Backend and db_service `CreateOrderRequest` models are identical
- **Flexibility**: Frontend can send minimal data (just `userId` and `items`) or complete data with all optional fields
- **Auto-calculation**: Backend automatically sets `totalItems` if not provided
- **Validation**: DB service validate user existence and product availability in db

#### **Prediction Endpoints (`/api/predictions/*`)**
- **Response Fields**: `userId`, `productId`, `productName`
- **ID Types**: `userId` is UUID4 string

**Example Prediction Response:**
```json
{
  "success": true,
  "data": {
    "userId": "456",
    "predictions": [
      {
        "productId": 123,
        "productName": "Organic Milk",
        "score": 0.8
      }
    ],
    "total": 1
  }
}
```

___
##	Suggested Steps for Frontend to Display Notifications for order status updates and cart reminder on login;
___
A. On Login:

- Send login request (`POST /api/users/login`) with credentials.   V

- On success:   V

  - Route user to dashboard/home.   V

B. Immediately After Login:

- Fire parallel API requests:

   - `/api/users/{user_id}/order-status-notifications` (get orders with changed status)

   - If in login response returned `hasActiveCart=True`;
       `/api/cart/{user_id}` (get cart, if exists)
   
   - Optional [render notifications and cart];
       - For the notification bell icon at the top of the page;
           - show a faded badge for the number of notifications.
             (same for cart badge).

C. When Data Arrives:
-  Show notifications:
   - For each changed order, show a clickable notification (e.g “Order #1234 shipped!” V).
      - On click, navigate to `/orders/{order_id}` (`/api/orders/{order_id}`).
       - Show cart reminder notification:
           - If cart exists and isn't empty, show reminder (e.g., "You have 3 items in your cart from 2 days ago." V)  
           On click, navigate to `/cart/{user_id}` (`/api/cart/{user_id}`).   V
       - Optional [render notifications and cart];
           - Notification bell updates;
               - badge shows “2” if there are 2 new notifications (order status changes, order scheduler etc.).  
                 (same for the cart icon (shows count of cart items once loaded)).
___
