# backend/app/routers/users.py
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from pydantic import BaseModel, EmailStr, conint, Field
from ..models.base import APIResponse
from ..services.database_service import db_service
from datetime import datetime, UTC

router = APIRouter(prefix="/users", tags=["Users"])

# --- Helper for Centralized Error Handling ---

def _handle_db_service_error(result: dict, entity_id: Optional[str] = None, operation: str = "operation",
                             default_error: str = "Operation failed"):
    """
    Centralized handler for db_service errors.
    Raises HTTPException with appropriate status code and detail message.
    """
    if not result.get("success", False):
        error_msg = result.get("error", default_error).lower()
        print(f"db_service {operation} failed with error: {error_msg}")

        status_code = 500
        detail = f"An internal server error occurred during {operation}."

        if "user not found" in error_msg:
            status_code = 404
            detail = f"User {entity_id} not found" if entity_id else "User not found"
        elif "email address already exists" in error_msg:
            status_code = 409
            detail = "Email address already exists"
        elif "username already exists" in error_msg:
            status_code = 409
            detail = "Username already exists"
        elif "current password is incorrect" in error_msg:
            status_code = 400
            detail = "Current password is incorrect"
        elif "password incorrect" in error_msg:
            status_code = 400
            detail = "Password incorrect"
        elif "invalid email or password" in error_msg:
            status_code = 401
            detail = "Invalid email or password"
        elif "database error" in error_msg:
            status_code = 503
            detail = "Service temporarily unavailable"
        else:
            # Fallback for other db_service errors
            detail = f"{operation.capitalize()} failed"

        raise HTTPException(status_code=status_code, detail=detail, headers={"X-Handled-Error": "true"})

def _handle_unhandled_http_exception(e: HTTPException, operation_error_message: str):
    """
    Helper to handle unhandled HTTPExceptions that don't have the X-Handled-Error header.
    Logs and sanitizes unknown HTTPExceptions.
    """
    # Check if this HTTPException was handled by the centralized handler
    if e.headers and e.headers.get("X-Handled-Error") == "true":
        raise
    else:
        # Log and sanitize unknown HTTPExceptions
        print(f"Unknown HTTPException caught: {str(e)}")
        raise HTTPException(status_code=500, detail=operation_error_message)

# --- Pydantic Models ---

class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    user_id: int
    first_name: str
    last_name: str
    email_address: str
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_next_scheduled_time: Optional[datetime] = None
    pending_order_notification: Optional[bool] = None
    order_notifications_via_email: Optional[bool] = None
    last_notification_sent_at: Optional[datetime] = None

class CreateUserRequest(BaseModel):
    """Create user request model"""
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email_address: EmailStr = Field(..., alias="email")  # Accept both "email" and "email_address"
    password: str
    phone_number: Optional[str] = Field(None, alias="phone")
    street_address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    # Notification-related fields that user is allowed to configure
    days_between_order_notifications: Optional[int] = 7
    order_notifications_via_email: Optional[bool] = False
    order_notifications_start_date_time: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))

class UpdateUserRequest(BaseModel):
    """Update user request model"""
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    """Update password request model"""
    current_password: str
    new_password: str

class UpdateEmailRequest(BaseModel):
    """Update email request model"""
    current_password: str
    new_email_address: EmailStr

class UpdateNotificationSettingsRequest(BaseModel):
    """Update notification settings request model"""
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_via_email: Optional[bool] = None

class LoginRequest(BaseModel):
    """Login request model"""
    email_address: EmailStr
    password: str

class DeleteUserRequest(BaseModel):
    """Delete user request model, requires password for verification"""
    password: str

# --- Routes ---

@router.get("/login", response_model=APIResponse)
async def demo_login() -> APIResponse:
    """Demo login endpoint - returns random demo user with ML predictions"""
    import random
    
    # Working demo users with ML predictions
    demo_users = [
        {"user_id": 688, "first_name": "Demo", "last_name": "User 688", "email": "user688@timele-demo.com"},
        {"user_id": 82420, "first_name": "Demo", "last_name": "User 82420", "email": "user82420@timele-demo.com"},
        {"user_id": 43682, "first_name": "Demo", "last_name": "User 43682", "email": "user43682@timele-demo.com"},
        {"user_id": 39993, "first_name": "Demo", "last_name": "User 39993", "email": "user39993@timele-demo.com"}
    ]
    
    # Select random demo user
    selected_user = random.choice(demo_users)
    
    return APIResponse(
        message="Demo login successful",
        data={
            "user_id": str(selected_user["user_id"]),
            "first_name": selected_user["first_name"],
            "last_name": selected_user["last_name"],
            "email_address": selected_user["email"],
            "phone_number": f"+1-555-0{selected_user['user_id']}",
            "street_address": f"{selected_user['user_id']} Demo Street",
            "city": "Demo City",
            "postal_code": str(selected_user['user_id']),
            "country": "US",
            "demo_user": True,
            "ml_predictions_available": True
        }
    )

@router.get("/{user_id}", response_model=APIResponse)
async def get_user_profile(user_id: str) -> APIResponse:
    """Get user profile by ID"""
    try:
        # Get user from db_service
        user_result = await db_service.get_entity("users", user_id)
        _handle_db_service_error(user_result, user_id, "accessing user profile", "Accessing user profile failed")
        
        user_data = user_result.get("data", [])

        if not user_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found", headers={"X-Handled-Error": "true"})
        
        # Convert to UserResponse model (excluding sensitive data)
        user_row = user_data[0]
        user_response = UserResponse(**user_row)
        
        return APIResponse(
            message="User profile retrieved successfully",
            data=user_response
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Accessing user profile failed due to server error")
    except Exception as e:
        print(f"Accessing user profile failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Accessing user profile failed due to a server error")

@router.post("/register", response_model=APIResponse)
# TODO: return 201 on creation of resource, make sure frontend ok w/ the change.
# @router.post("/register", response_model=APIResponse, status_code=201)
async def register_user(user_request: CreateUserRequest) -> APIResponse:
    """Create a new user account"""
    try:
        create_result = await db_service.create_entity("users", user_request.model_dump(mode="json")) # mode="json" serializes datetimes as ISO 8601 strings
        _handle_db_service_error(create_result, operation="registration", default_error="Failed to create user")
        
        created_data = create_result.get("data", [])

        if not created_data:
            raise HTTPException(status_code=500, detail="User creation returned no data", headers={"X-Handled-Error": "true"})
        
        # Return created user info (without password)
        created_user = created_data[0]
        user_response = UserResponse(**created_user)

        return APIResponse(
            message="User registered successfully",
            data=user_response
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Registration failed due to server error")
    except Exception as e:
        # Handle common database errors
        error_msg = str(e).lower()
        print(f"Registration failed with unhandled error: {error_msg}")
        if "unique" in error_msg and "email" in error_msg:
            raise HTTPException(status_code=409, detail="Email address already exists")
        elif "unique" in error_msg and "name" in error_msg:
            raise HTTPException(status_code=409, detail="Username already exists")
        # Check for specific service communication issues
        elif "connection" in error_msg or "timeout" in error_msg:
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        elif "json" in error_msg or "decode" in error_msg:
            raise HTTPException(status_code=502, detail="Invalid service response")
        else:
            # Generic service error - don't leak details
            raise HTTPException(status_code=500, detail="Registration failed due to a server error")

@router.put("/{user_id}", response_model=APIResponse)
async def update_user_profile(user_id: str, user_request: UpdateUserRequest) -> APIResponse:
    """Update user profile details"""
    try:
        # Prepare update data (only include non-None fields)
        update_data = {}
        for field, value in user_request.model_dump(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update", headers={"X-Handled-Error": "true"})
        
        # Update user in database using generic update_entity
        update_result = await db_service.update_entity("users", user_id, update_data)
        _handle_db_service_error(update_result, user_id, "user update", "Failed to update user")
        
        updated_data = update_result.get("data", [])

        if not updated_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found or no changes made", headers={"X-Handled-Error": "true"})
        
        updated_user = updated_data[0]
        user_response = UserResponse(**updated_user)
        
        return APIResponse(
            message="User profile updated successfully",
            data=user_response
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "User update failed due to a server error")
    except Exception as e:
        # Handle common database errors
        error_msg = str(e).lower()
        print(f"User update failed with error: {error_msg}")
        if "unique" in error_msg and "email" in error_msg:
            raise HTTPException(status_code=409, detail="Email address already exists")
        elif "unique" in error_msg and "name" in error_msg:
            raise HTTPException(status_code=409, detail="Username already exists")
        else:
            raise HTTPException(status_code=500, detail=f"User update failed due to a server error")

@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str, request: DeleteUserRequest = Body(...)) -> APIResponse:
    """Delete a user account after verifying password."""
    try:
        # The db_service expects the password in the request body for verification.
        delete_result = await db_service.delete_entity("users", user_id, data=request.model_dump(),
                                                       headers={"Content-Type": "application/json"}) # Explicitly set content type for DELETE with JSON body
        _handle_db_service_error(delete_result, user_id, "user deletion", "Failed to delete user")
        
        deleted_data = delete_result.get("data", [])

        if not deleted_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found", headers={"X-Handled-Error": "true"})
        
        return APIResponse(
            message=f"User {user_id} deleted successfully",
            data={"user_id": user_id, "deleted": True}
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "User deletion failed due to a server error")
    except Exception as e:
        print(f"Deletion failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Deletion failed due to a server error")

@router.put("/{user_id}/password", response_model=APIResponse)
async def update_user_password(user_id: str, password_request: UpdatePasswordRequest) -> APIResponse:
    """Update user password"""
    try:
        # db_service handles password hashing with Argon2id
        update_data = password_request.model_dump()

        # Update password in database; db_service handles hashing
        update_result = await db_service.update_entity("users", user_id, update_data, sub_resource="password")
        _handle_db_service_error(update_result, user_id, "password update", "Failed to update password")
        
        updated_data = update_result.get("data", [])

        if not updated_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found", headers={"X-Handled-Error": "true"})
        
        return APIResponse(
            message="Password updated successfully",
            data={"user_id": user_id, "password_updated": True}
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Password update failed due to a server error")
    except Exception as e:
        print(f"Password update failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password update failed due to a server error")

@router.post("/login", response_model=APIResponse)
async def login_user(login_request: LoginRequest) -> APIResponse:
    """Real login endpoint using db_service"""
    try:
        # Use db_service to authenticate user
        login_result = await db_service.create_entity("users/login", login_request.model_dump())
        _handle_db_service_error(login_result, operation="login", default_error="Login failed")
        
        login_data = login_result.get("data", [])

        if not login_data:
            raise HTTPException(status_code=401, detail="Invalid email or password", headers={"X-Handled-Error": "true"})
        
        # Convert to UserResponse model (excluding sensitive data)
        user_data = login_data[0]
        user_response = UserResponse(**user_data)
        
        return APIResponse(
            message="Login successful",
            data=user_response
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Login failed due to a server error")
    except Exception as e:
        print(f"Login failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed due to a server error")

@router.get("/{user_id}/notification-settings", response_model=APIResponse)
async def get_notification_settings(user_id: str) -> APIResponse:
    """Get user notification settings"""
    try:
        # Use db_service to get notification settings
        # Use get_entity with sub_resource parameter
        settings_result = await db_service.get_entity("users", user_id, sub_resource="notification-settings")
        _handle_db_service_error(settings_result, user_id, "get notification settings", "Failed to get notification settings")
        
        settings_data = settings_result.get("data", [])     # no data just means user has no notification data stored
        
        return APIResponse(
            message="Notification settings retrieved successfully",
            data=settings_data[0]
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to get notification settings due to a server error")
    except Exception as e:
        print(f"Failed to get notification settings with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification settings due to a server error")

@router.put("/{user_id}/notification-settings", response_model=APIResponse)
async def update_notification_settings(user_id: str, settings_request: UpdateNotificationSettingsRequest) -> APIResponse:
    """Update user notification settings"""
    try:
        # Prepare update data (only include non-None fields)
        update_data = {}
        for field, value in settings_request.model_dump(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update", headers={"X-Handled-Error": "true"})

        # Use db_service to update notification settings
        # Use update_entity with sub_resource parameter
        update_result = await db_service.update_entity("users", user_id, update_data,
                                                       sub_resource="notification-settings")
        _handle_db_service_error(update_result, user_id, "update notification settings", "Failed to update notification settings")
        
        updated_data = update_result.get("data", [])

        if not updated_data:
            return APIResponse(message="No changes made", data={})
        
        return APIResponse(
            message="Notification settings updated successfully",
            data=updated_data[0]
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to update notification settings due to a server error")
    except Exception as e:
        print(f"Failed to update notification settings with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification settings due to a server error")

@router.put("/{user_id}/email", response_model=APIResponse)
async def update_user_email(user_id: str, email_request: UpdateEmailRequest) -> APIResponse:
    """Update user email address"""
    try:
        # db_service handles password verification and email validation
        update_data = email_request.model_dump()

        # Update email in database; db_service handles verification
        update_result = await db_service.update_entity("users", user_id, update_data, sub_resource="email")
        _handle_db_service_error(update_result, user_id, "email update", "Failed to update email address")

        updated_data = update_result.get("data", [])

        if not updated_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found", headers={"X-Handled-Error": "true"})

        return APIResponse(
            message="Email address updated successfully",
            data={
                "user_id": user_id,
                "email_address": updated_data[0]["email_address"]
            }
        )
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Email update failed due to a server error")
    except Exception as e:
        print(f"Email update failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Email update failed due to a server error")

@router.post("/logout", response_model=APIResponse)
async def logout_user() -> APIResponse:
    """Logout endpoint; placeholder until JWT implementation"""
    return APIResponse(
        message="Logout successful",
        data={"logged_out": True}
    )

