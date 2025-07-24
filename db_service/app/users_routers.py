# app/users_routers.py

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from .db_core.database import SessionLocal
from .db_core.models import User
from pydantic import BaseModel, EmailStr
from typing import Optional
# Removed UUID imports since we're using integer user_ids
# import hashlib
import bcrypt

router = APIRouter(prefix="/users", tags=["users"])

def hash_password(password: str) -> str:
    # return hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def authenticate_user(email: str, password: str):
    session = SessionLocal()
    user = session.query(User).filter_by(email_address=email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

class CreateUserRequest(BaseModel):
    name: str
    email_address: EmailStr
    password: str
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user_request: CreateUserRequest):
    session = SessionLocal()
    try:
        # Check for duplicate email or name
        if session.query(User).filter_by(email_address=user_request.email_address).first():
            raise HTTPException(status_code=409, detail="Email address already exists")
        # if session.query(User).filter_by(name=user_request.name).first():
        #     raise HTTPException(status_code=409, detail="Username already exists")

        hashed_pw = hash_password(user_request.password)
        # Get next available user_id (auto-increment would be better but this works)
        max_id = session.query(func.max(User.user_id)).scalar() or 0
        next_id = max_id + 1
        
        db_user = User(
            user_id=next_id,
            name=user_request.name,
            email_address=user_request.email_address,
            hashed_password=hashed_pw,
            phone_number=user_request.phone_number,
            street_address=user_request.street_address,
            city=user_request.city,
            postal_code=user_request.postal_code,
            country=user_request.country
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return {
            "user_id": db_user.user_id,
            "name": db_user.name,
            "email_address": db_user.email_address
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user")
    finally:
        session.close()


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/{user_id}/password", status_code=status.HTTP_200_OK)
def update_user_password(
        user_id: int,
        payload: UpdatePasswordRequest
):
    session = SessionLocal()
    try:
        # Fetch user
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash and set new password
        new_hashed = hash_password(payload.new_password)
        user.hashed_password = new_hashed
        session.commit()
        return {"message": "Password updated successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating password: {e}")
        raise HTTPException(status_code=500, detail="Error updating password")
    finally:
        session.close()

class UpdateEmailRequest(BaseModel):
    current_password: str
    new_email_address: EmailStr

@router.post("/{user_id}/email", status_code=status.HTTP_200_OK)
def update_user_email(
        user_id: int,
        payload: UpdateEmailRequest
):
    session = SessionLocal()
    try:
        # Fetch user
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Check for duplicate email (must not already exist)
        existing = session.query(User).filter(
            User.email_address == payload.new_email_address,
            User.user_id != user_id  # Exclude current user
        ).first()
        if existing:
            print("Email address already in use by another user.")
            raise HTTPException(status_code=409, detail="Invalid update request.")

        # Update email
        user.email_address = payload.new_email_address
        session.commit()
        return {"message": "Email address updated successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating email: {e}")
        raise HTTPException(status_code=500, detail="Error updating email address")
    finally:
        session.close()

@router.get("/{user_id}")
def get_user(user_id: int):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email_address": user.email_address,
            "phone_number": user.phone_number,
            "street_address": user.street_address,
            "city": user.city,
            "postal_code": user.postal_code,
            "country": user.country,
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user")
    finally:
        session.close()


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

# Only non-credential fields can be updated here.
# Attempting to update email/password will have no effect.
@router.patch("/{user_id}")
def update_user(user_id: int, payload: UpdateUserRequest):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Update allowed fields
        for field, value in update_data.items():
            setattr(user, field, value)
        session.commit()
        return {"message": "User updated successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user")
    finally:
        session.close()


class DeleteUserRequest(BaseModel):
    password: str


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, payload: DeleteUserRequest):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=403, detail="Password incorrect")
        session.delete(user)
        session.commit()
        return {"message": "User deleted successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting user")
    finally:
        session.close()
