# backend/app/routers/users.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, EmailStr
from ..models.base import APIResponse
from ..services.database_service import db_service
import hashlib

router = APIRouter(prefix="/api/users", tags=["Users"])

class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    user_id: str
    name: str
    email_address: str
    phone_number: str
    street_address: str
    city: str
    postal_code: str
    country: str

class CreateUserRequest(BaseModel):
    """Create user request model"""
    name: str
    email_address: EmailStr
    password: str
    phone_number: str
    street_address: str
    city: str
    postal_code: str
    country: str

class UpdateUserRequest(BaseModel):
    """Update user request model"""
    name: Optional[str] = None
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

def hash_password(password: str) -> str:
    """Simple password hashing (use proper hashing in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

@router.get("/{user_id}", response_model=APIResponse)
async def get_user_profile(user_id: str) -> APIResponse:
    """Get user profile by ID"""
    try:
        # Get user from database
        user_result = await db_service.get_user_by_id(user_id)
        
        if not user_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        user_data = user_result.get("data", [])
        
        if not user_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Convert to UserResponse model (excluding sensitive data)
        user_row = user_data[0]
        user = UserResponse(
            user_id=str(user_row["user_id"]),
            name=user_row["name"],
            email_address=user_row["email_address"],
            phone_number=user_row["phone_number"],
            street_address=user_row["street_address"],
            city=user_row["city"],
            postal_code=user_row["postal_code"],
            country=user_row["country"]
        )
        
        return APIResponse(
            message="User profile retrieved successfully",
            data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register", response_model=APIResponse)
async def register_user(user_request: CreateUserRequest) -> APIResponse:
    """Create a new user account"""
    try:
        # Hash the password
        hashed_password = hash_password(user_request.password)
        
        # Prepare user data
        user_data = {
            "name": user_request.name,
            "hashed_password": hashed_password,
            "email_address": user_request.email_address,
            "phone_number": user_request.phone_number,
            "street_address": user_request.street_address,
            "city": user_request.city,
            "postal_code": user_request.postal_code,
            "country": user_request.country
        }
        
        # Create user in database
        create_result = await db_service.create_user(user_data)
        
        if not create_result.get("success", True):
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        created_data = create_result.get("data", [])
        
        if not created_data:
            raise HTTPException(status_code=500, detail="User creation returned no data")
        
        # Return created user info (without password)
        created_user = created_data[0]
        
        return APIResponse(
            message="User registered successfully",
            data={
                "user_id": str(created_user["user_id"]),
                "name": created_user["name"],
                "email_address": created_user["email_address"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        # Handle common database errors
        error_msg = str(e).lower()
        if "unique" in error_msg and "email" in error_msg:
            raise HTTPException(status_code=400, detail="Email address already exists")
        elif "unique" in error_msg and "name" in error_msg:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.put("/{user_id}", response_model=APIResponse)
async def update_user_profile(user_id: str, user_request: UpdateUserRequest) -> APIResponse:
    """Update user profile details"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        
        if not user_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        if not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Prepare update data (only include non-None fields)
        update_data = {}
        for field, value in user_request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update user in database
        update_result = await db_service.update_user(user_id, update_data)
        
        if not update_result.get("success", True):
            raise HTTPException(status_code=500, detail="Failed to update user")
        
        updated_data = update_result.get("data", [])
        
        if not updated_data:
            raise HTTPException(status_code=500, detail="User update returned no data")
        
        updated_user = updated_data[0]
        
        return APIResponse(
            message="User profile updated successfully",
            data={
                "user_id": str(updated_user["user_id"]),
                "name": updated_user["name"],
                "email_address": updated_user["email_address"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        # Handle common database errors
        error_msg = str(e).lower()
        if "unique" in error_msg and "email" in error_msg:
            raise HTTPException(status_code=400, detail="Email address already exists")
        elif "unique" in error_msg and "name" in error_msg:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str) -> APIResponse:
    """Delete a user account"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        
        if not user_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        if not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Delete user from database
        delete_result = await db_service.delete_user(user_id)
        
        if not delete_result.get("success", True):
            raise HTTPException(status_code=500, detail="Failed to delete user")
        
        deleted_data = delete_result.get("data", [])
        
        if not deleted_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return APIResponse(
            message=f"User {user_id} deleted successfully",
            data={
                "user_id": user_id,
                "deleted": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.post("/{user_id}/password", response_model=APIResponse)
async def update_user_password(user_id: str, password_request: UpdatePasswordRequest) -> APIResponse:
    """Update user password"""
    try:
        # Verify user exists and get current password
        user_result = await db_service.get_user_by_id(user_id)
        
        if not user_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        user_data = user_result.get("data", [])
        
        if not user_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # TODO: In a real implementation, you would:
        # 1. Verify the current password matches the stored hash
        # 2. Implement proper password validation rules
        # 3. Use a secure hashing algorithm like bcrypt
        
        # Hash the new password
        new_hashed_password = hash_password(password_request.new_password)
        
        # Update password in database
        update_result = await db_service.update_user_password(user_id, new_hashed_password)
        
        if not update_result.get("success", True):
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        updated_data = update_result.get("data", [])
        
        if not updated_data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return APIResponse(
            message="Password updated successfully",
            data={
                "user_id": user_id,
                "password_updated": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password update failed: {str(e)}")
