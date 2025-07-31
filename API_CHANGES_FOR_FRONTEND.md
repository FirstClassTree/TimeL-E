# API Changes for Frontend Developers

## BREAKING CHANGE: Complete camelCase Support for Frontend (see below)

The backend now provides **complete camelCase support** for all frontend-facing endpoints.  
All request and response field names are now consistently camelCase for the frontend, while maintaining snake_case internally.

## Overview
This document details all API changes made to the backend endpoints including:
- Major user management system overhaul with security enhancements and notification features
- Complete camelCase standardization for frontend communication
- Cart, orders, and product endpoint camelCase support

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
    "lastNotificationSentAt": "2025-07-29T10:00:00Z"
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
  "email": "john@example.com",
  "password": "securepassword",
  "phone": "+1-555-0123",
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
  "email": "john@example.com",
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
  "email": "johnsmith@example.com",
  "phone": "+1-555-0456"
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
    // ... full user profile with notification fields
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

#### **Cart Endpoints (`/api/cart/*`)**   --scheduled next for full implementation--
- **Request Fields**: `productId`, `quantity` (instead of `product_id`)
- **Response Fields**: `userId`, `totalItems`, `totalQuantity`, `productId`, `productName`, `aisleName`, `departmentName`

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

#### **Order Endpoints (`/api/orders/*`)**
- **Request Fields**: `userId`, `productId`, `quantity`
- **Response Fields**: `orderId`, `userId`, `orderNumber`, `totalItems`, `productId`, `productName`

**Example Order Request:**
```json
{
    "userId": 456,
    "items": [
      {
        "productId": 123,
        "quantity": 2
      }
    ]
}
```

#### **Prediction Endpoints (`/api/predictions/*`)**
- **Response Fields**: `userId`, `productId`, `productName`

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
