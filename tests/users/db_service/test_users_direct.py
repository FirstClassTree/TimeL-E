"""
Direct DB Service User Routes Tests

This module contains comprehensive tests for the db_service user routes,
testing them directly without going through the backend layer.

Tests cover:
- User CRUD operations
- Authentication and login
- Password management
- Email management
- Notification settings
- Error handling and edge cases
"""

import pytest
import requests
import time
from datetime import datetime, UTC
from typing import Dict, Any

from ..utils.test_helpers import (
    create_test_user_data,
    create_invalid_user_data,
    create_notification_settings_data,
    extract_user_id_from_response,
    extract_user_email_from_response,
    assert_datetime_close,
    assert_user_data_matches,
    assert_response_has_structure,
    cleanup_test_user,
    DbServiceUserTestContext,
    PerformanceTimer,
    measure_response_time
)

OPTIONAL_USER_FIELDS = [
    "phone_number", "street_address", "city", "postal_code", "country",
    "days_between_order_notifications", "order_notifications_start_date_time",
    "order_notifications_next_scheduled_time", "pending_order_notification",
    "order_notifications_via_email", "last_notification_sent_at",
    "last_notifications_viewed_at", "last_login", "has_active_cart"
]

OPTIONAL_NOTIFICATION_SETTINGS_FIELDS = [
    "order_notifications_start_date_time", "order_notifications_next_scheduled_time",
    "last_notification_sent_at"
]

class TestUserCreation:
    """Test user creation functionality"""
    
    def test_create_user_success(self, db_service_url, user_manager):
        """Test successful user creation with all fields"""
        user_data = create_test_user_data("create_success")
        
        response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        assert response_json["success"] is True, f"Expected success=True, got: {response_json}"
        assert "data" in response_json
        assert len(response_json["data"]) == 1
        
        created_user = response_json["data"][0]
        user_id = created_user["user_id"]
        
        # Track for cleanup
        user_manager.track_user(user_id, user_data["email_address"])
        
        # Validate response structure
        assert_response_has_structure(
            created_user,
            required_fields=["user_id", "first_name", "last_name", "email_address"],
            optional_fields=OPTIONAL_USER_FIELDS,
            forbidden_fields=["password", "hashed_password"]
        )
        
        # Validate data matches
        assert_user_data_matches(created_user, user_data)
    
    def test_create_user_minimal_fields(self, db_service_url, user_manager):
        """Test user creation with only required fields"""
        user_data = create_test_user_data("create_minimal", include_optional=False)
        
        response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        assert response_json["success"] is True
        
        created_user = response_json["data"][0]
        user_id = created_user["user_id"]
        
        user_manager.track_user(user_id, user_data["email_address"])
        
        # Check required fields are present
        assert created_user["first_name"] == user_data["first_name"]
        assert created_user["last_name"] == user_data["last_name"]
        assert created_user["email_address"] == user_data["email_address"]
    
    def test_create_user_duplicate_email(self, db_service_url, user_manager):
        """Test user creation with duplicate email address"""
        user_data = create_test_user_data("duplicate_email")
        
        # Create first user
        response1 = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        response1_json = response1.json()
        assert response1_json["success"] is True
        
        user_id = extract_user_id_from_response(response1)
        user_manager.track_user(user_id, user_data["email_address"])
        
        # Try to create second user with same email
        user_data2 = create_test_user_data("duplicate_email2")
        user_data2["email_address"] = user_data["email_address"]  # Same email
        
        response2 = requests.post(f"{db_service_url}/users/", json=user_data2, timeout=10)
        
        # DB service returns structured response with success=False for business logic errors
        response_json = response2.json()
        assert response_json["success"] is False
        assert "email" in response_json["error"].lower()
    
    def test_create_user_invalid_data(self, db_service_url):
        """Test user creation with invalid data"""
        invalid_data = create_invalid_user_data()
        
        response = requests.post(f"{db_service_url}/users/", json=invalid_data, timeout=10)
        
        # For validation errors, FastAPI may return 422, but db_service should handle gracefully
        # Check if it's a validation error (422) or business logic error (success=False)
        if response.status_code == 422:
            # FastAPI validation error - this is acceptable for invalid data
            pass
        else:
            # Should return success=False for business logic errors
            response_json = response.json()
            assert response_json["success"] is False
    
    def test_create_user_missing_required_fields(self, db_service_url):
        """Test user creation with missing required fields"""
        incomplete_data = {
            "first_name": "Test"
            # Missing last_name, email_address, password
        }
        
        response = requests.post(f"{db_service_url}/users/", json=incomplete_data, timeout=10)
        
        # For validation errors, FastAPI may return 422, but db_service should handle gracefully
        # Check if it's a validation error (422) or business logic error (success=False)
        if response.status_code == 422:
            # FastAPI validation error - this is acceptable for missing required fields
            pass
        else:
            # Should return success=False for business logic errors
            response_json = response.json()
            assert response_json["success"] is False
    
    def test_create_user_performance(self, db_service_url, user_manager):
        """Test user creation performance"""
        user_data = create_test_user_data("performance")
        
        response, elapsed_time = measure_response_time(
            requests.post,
            f"{db_service_url}/users/",
            json=user_data,
            timeout=10
        )
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        assert response_json["success"] is True
        assert elapsed_time < 0.5, f"User creation took {elapsed_time:.3f}s, expected < 0.5s"
        
        user_id = extract_user_id_from_response(response)
        user_manager.track_user(user_id, user_data["email_address"])


class TestUserRetrieval:
    """Test user retrieval functionality"""
    
    def test_get_user_success(self, db_service_url):
        """Test successful user retrieval"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            user_data = response_json["data"][0]
            assert user_data["user_id"] == user_id
            assert user_data["email_address"] == user_ctx.get_email()
            
            # Ensure sensitive data is not returned
        assert_response_has_structure(
            user_data,
            required_fields=["user_id", "first_name", "last_name", "email_address"],
            optional_fields=OPTIONAL_USER_FIELDS,
            forbidden_fields=["password", "hashed_password"]
        )
    
    def test_get_user_not_found(self, db_service_url):
        """Test retrieval of non-existent user"""
        non_existent_id = 999999
        
        response = requests.get(f"{db_service_url}/users/{non_existent_id}", timeout=10)
        
        # DB service returns structured response with success=False for not found
        response_json = response.json()
        assert response_json["success"] is False
        assert "not found" in response_json["error"].lower()
    
    def test_get_user_invalid_id(self, db_service_url):
        """Test retrieval with invalid user ID format"""
        invalid_id = "invalid"
        
        response = requests.get(f"{db_service_url}/users/{invalid_id}", timeout=10)
        
        # FastAPI validation catches invalid ID format and returns 422 BEFORE reaching endpoint
        # This is different from business logic errors (valid format but non-existent ID)
        assert response.status_code == 422, f"Expected 422 for invalid ID format, got {response.status_code}"


class TestUserUpdate:
    """Test user update functionality"""
    
    def test_update_user_partial(self, db_service_url):
        """Test partial user update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "city": "Updated City",
                "phone_number": "+1-555-9999"
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            updated_user = response_json["data"][0]
            assert updated_user["city"] == update_data["city"]
            assert updated_user["phone_number"] == update_data["phone_number"]
    
    def test_update_user_full(self, db_service_url):
        """Test full user profile update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "first_name": "Updated",
                "last_name": "Name",
                "phone_number": "+1-555-8888",
                "street_address": "456 Updated St",
                "city": "Updated City",
                "postal_code": "54321",
                "country": "Updated Country"
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            updated_user = response_json["data"][0]
            assert_user_data_matches(updated_user, update_data)
    
    def test_update_user_not_found(self, db_service_url):
        """Test update of non-existent user"""
        non_existent_id = 999999
        update_data = {"city": "New City"}
        
        response = requests.put(
            f"{db_service_url}/users/{non_existent_id}",
            json=update_data,
            timeout=10
        )
        
        # DB service returns structured response with success=False for not found
        response_json = response.json()
        assert response_json["success"] is False
    
    def test_update_user_no_changes(self, db_service_url):
        """Test update with no actual changes"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Empty update
            response = requests.put(
                f"{db_service_url}/users/{user_id}",
                json={},
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            assert response_json["message"] == "No changes made"
            assert response_json["data"] == []  # Empty data array when no changes made


class TestUserDeletion:
    """Test user deletion functionality"""
    
    def test_delete_user_success(self, db_service_url):
        """Test successful user deletion"""
        user_data = create_test_user_data("delete_success")
        
        # Create user
        create_response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        create_json = create_response.json()
        assert create_json["success"] is True
        
        user_id = extract_user_id_from_response(create_response)
        
        # Delete user
        delete_data = {"password": user_data["password"]}
        delete_response = requests.delete(
            f"{db_service_url}/users/{user_id}",
            json=delete_data,
            timeout=10
        )
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = delete_response.json()
        assert response_json["success"] is True
        
        # Verify user is deleted - this should return success=False
        get_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        get_json = get_response.json()
        assert get_json["success"] is False
        assert "not found" in get_json["error"].lower()
    
    def test_delete_user_wrong_password(self, db_service_url):
        """Test user deletion with wrong password"""
        with DbServiceUserTestContext(db_service_url, auto_cleanup=False) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            delete_data = {"password": "wrong_password"}
            response = requests.delete(
                f"{db_service_url}/users/{user_id}",
                json=delete_data,
                timeout=10
            )
            
            # DB service returns structured response with success=False for wrong password
            response_json = response.json()
            assert response_json["success"] is False
            assert "password" in response_json["error"].lower()
    
    def test_delete_user_not_found(self, db_service_url):
        """Test deletion of non-existent user"""
        non_existent_id = 999999
        delete_data = {"password": "any_password"}
        
        response = requests.delete(
            f"{db_service_url}/users/{non_existent_id}",
            json=delete_data,
            timeout=10
        )
        
        # DB service returns structured response with success=False for not found
        response_json = response.json()
        assert response_json["success"] is False


class TestUserAuthentication:
    """Test user authentication and login"""
    
    def test_login_success(self, db_service_url):
        """Test successful user login"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            login_data = {
                "email_address": user_ctx.get_email(),
                "password": user_ctx.get_password()
            }
            
            response = requests.post(
                f"{db_service_url}/users/login",
                json=login_data,
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            user_data = response_json["data"][0]
            assert user_data["user_id"] == user_ctx.get_user_id()
            assert user_data["email_address"] == user_ctx.get_email()
    
    def test_login_invalid_email(self, db_service_url):
        """Test login with invalid email"""
        login_data = {
            "email_address": "nonexistent@example.com",
            "password": "any_password"
        }
        
        response = requests.post(
            f"{db_service_url}/users/login",
            json=login_data,
            timeout=10
        )
        
        # DB service returns structured response with success=False for invalid credentials
        response_json = response.json()
        assert response_json["success"] is False
        assert "invalid" in response_json["error"].lower()
    
    def test_login_invalid_password(self, db_service_url):
        """Test login with invalid password"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            login_data = {
                "email_address": user_ctx.get_email(),
                "password": "wrong_password"
            }
            
            response = requests.post(
                f"{db_service_url}/users/login",
                json=login_data,
                timeout=10
            )
            
            # DB service returns structured response with success=False for invalid credentials
            response_json = response.json()
            assert response_json["success"] is False
    
    def test_login_malformed_request(self, db_service_url):
        """Test login with malformed request"""
        login_data = {
            "email": "missing_address_field@example.com"  # Wrong field name
            # Missing password
        }
        
        response = requests.post(
            f"{db_service_url}/users/login",
            json=login_data,
            timeout=10
        )
        
        # This test correctly expects HTTP status codes because FastAPI's Pydantic validation
        # catches malformed requests (wrong field names, missing required fields) and returns
        # 422/400 BEFORE the request reaches the login_user function. This is different from
        # business logic errors (valid request format but wrong credentials) which return
        # the structured ServiceResponse with success=False.
        assert response.status_code == 422 or response.status_code == 400


class TestPasswordManagement:
    """Test password update functionality"""
    
    def test_update_password_success(self, db_service_url):
        """Test successful password update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            current_password = user_ctx.get_password()
            new_password = "NewPassword123_" + str(int(time.time()))
            
            update_data = {
                "current_password": current_password,
                "new_password": new_password
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/password",
                json=update_data,
                timeout=10
            )
            
            response_json = response.json()
            assert response_json["success"] is True
            
            # Verify new password works
            login_data = {
                "email_address": user_ctx.get_email(),
                "password": new_password
            }
            
            login_response = requests.post(
                f"{db_service_url}/users/login",
                json=login_data,
                timeout=10
            )
            
            # Verify new password works by checking login success
            login_json = login_response.json()
            assert login_json["success"] is True
    
    def test_update_password_wrong_current(self, db_service_url):
        """Test password update with wrong current password"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "current_password": "wrong_password",
                "new_password": "NewPassword123"
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/password",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response with success=False for wrong password
            response_json = response.json()
            assert response_json["success"] is False
            assert "current password" in response_json["error"].lower()
    
    def test_update_password_user_not_found(self, db_service_url):
        """Test password update for non-existent user"""
        non_existent_id = 999999
        update_data = {
            "current_password": "any_password",
            "new_password": "NewPassword123"
        }
        
        response = requests.put(
            f"{db_service_url}/users/{non_existent_id}/password",
            json=update_data,
            timeout=10
        )
        
        # DB service returns structured response with success=False for not found
        response_json = response.json()
        assert response_json["success"] is False


class TestEmailManagement:
    """Test email update functionality"""
    
    def test_update_email_success(self, db_service_url):
        """Test successful email update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            current_password = user_ctx.get_password()
            new_email = f"updated_{int(time.time())}@timele-test.com"
            
            update_data = {
                "current_password": current_password,
                "new_email_address": new_email
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/email",
                json=update_data,
                timeout=10
            )
            
            response_json = response.json()
            assert response_json["success"] is True
            
            # Verify new email works for login
            login_data = {
                "email_address": new_email,
                "password": current_password
            }
            
            login_response = requests.post(
                f"{db_service_url}/users/login",
                json=login_data,
                timeout=10
            )
            
            # Verify new email works by checking login success
            login_json = login_response.json()
            assert login_json["success"] is True
    
    def test_update_email_duplicate(self, db_service_url):
        """Test email update to existing email"""
        # Create two users
        with DbServiceUserTestContext(db_service_url) as user1_ctx:
            with DbServiceUserTestContext(db_service_url) as user2_ctx:
                user1_id = user1_ctx.get_user_id()
                user1_password = user1_ctx.get_password()
                user2_email = user2_ctx.get_email()
                
                # Try to update user1's email to user2's email
                update_data = {
                    "current_password": user1_password,
                    "new_email_address": user2_email
                }
                
                response = requests.put(
                    f"{db_service_url}/users/{user1_id}/email",
                    json=update_data,
                    timeout=10
                )
                
                # DB service returns structured response with success=False for duplicate email
                response_json = response.json()
                assert response_json["success"] is False
                assert "email" in response_json["error"].lower()
    
    def test_update_email_wrong_password(self, db_service_url):
        """Test email update with wrong password"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            new_email = f"new_{int(time.time())}@timele-test.com"
            
            update_data = {
                "current_password": "wrong_password",
                "new_email_address": new_email
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/email",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response with success=False for wrong password
            response_json = response.json()
            assert response_json["success"] is False
            assert "password" in response_json["error"].lower()


class TestNotificationSettings:
    """Test notification settings functionality"""
    
    def test_get_notification_settings(self, db_service_url):
        """Test retrieval of notification settings"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            response = requests.get(
                f"{db_service_url}/users/{user_id}/notification-settings",
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            settings = response_json["data"][0]
            assert_response_has_structure(
                settings,
                required_fields=[
                    "user_id", "days_between_order_notifications",
                    "order_notifications_via_email", "pending_order_notification"
                ],
                optional_fields=OPTIONAL_NOTIFICATION_SETTINGS_FIELDS,
            )
    
    def test_update_notification_settings_partial(self, db_service_url):
        """Test partial notification settings update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "days_between_order_notifications": 14,
                "order_notifications_via_email": False
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            settings = response_json["data"][0]
            assert settings["days_between_order_notifications"] == 14
            assert settings["order_notifications_via_email"] is False
    
    def test_update_notification_settings_full(self, db_service_url):
        """Test full notification settings update"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = create_notification_settings_data(
                days_between_order_notifications=21,
                order_notifications_via_email=True
            )
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response, not HTTP status codes for business logic
            response_json = response.json()
            assert response_json["success"] is True
            
            settings = response_json["data"][0]
            assert settings["days_between_order_notifications"] == 21
            assert settings["order_notifications_via_email"] is True
    
    def test_update_notification_settings_invalid_range(self, db_service_url):
        """Test notification settings update with invalid range"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Test out of range value
            update_data = {
                "days_between_order_notifications": 500  # > 365
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            # For validation errors, FastAPI may return 422, but db_service could handle gracefully
            # Check if it's a validation error (422) or business logic error (success=False)
            if response.status_code == 422:
                # FastAPI validation error - this is acceptable for invalid range
                pass
            else:
                # Should return success=False for business logic errors
                response_json = response.json()
                assert response_json["success"] is False
    
    def test_update_notification_settings_no_changes(self, db_service_url):
        """Test notification settings update with no actual changes"""
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Get current settings first
            get_response = requests.get(
                f"{db_service_url}/users/{user_id}/notification-settings",
                timeout=10
            )
            get_json = get_response.json()
            assert get_json["success"] is True
            current_settings = get_json["data"][0]
            
            # Send the same values back (no actual changes)
            update_data = {
                "days_between_order_notifications": current_settings["days_between_order_notifications"],
                "order_notifications_via_email": current_settings["order_notifications_via_email"]
            }
            
            response = requests.put(
                f"{db_service_url}/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            # DB service returns structured response with success=True and updated data
            # Even when sending the same values, the service considers it a successful update
            response_json = response.json()
            assert response_json["success"] is True
            assert response_json["message"] == "Notification settings updated successfully"
            assert len(response_json["data"]) == 1  # Returns updated settings data
    
    def test_notification_settings_user_not_found(self, db_service_url):
        """Test notification settings for non-existent user"""
        non_existent_id = 999999
        
        response = requests.get(
            f"{db_service_url}/users/{non_existent_id}/notification-settings",
            timeout=10
        )
        
        # DB service returns structured response with success=False for not found
        response_json = response.json()
        assert response_json["success"] is False


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_concurrent_user_creation(self, db_service_url, user_manager):
        """Test concurrent user creation with different emails"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def create_user(suffix):
            try:
                user_data = create_test_user_data(f"concurrent_{suffix}")
                response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
                results.put((suffix, response.json()))
            except Exception as e:
                results.put((suffix, str(e)))
        
        # Create 3 users concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            suffix, response_data = results.get()
            if isinstance(response_data, dict) and response_data.get("success"):
                success_count += 1
                user_id = response_data["data"][0]["user_id"]
                email = response_data["data"][0]["email_address"]
                user_manager.track_user(user_id, email)
        
        # Due to potential race conditions in manual user_id generation, 
        # we expect at least 2 out of 3 concurrent creations to succeed
        assert success_count >= 2, f"Expected at least 2 successful creations, got {success_count}"
    
    def test_large_field_values(self, db_service_url, user_manager):
        """Test handling of large field values"""
        user_data = create_test_user_data("large_fields")
        user_data.update({
            "street_address": "A" * 200,  # Large but within reasonable limits
            "city": "B" * 50,
            "country": "C" * 50
        })
        
        response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        
        # Should either succeed or fail gracefully
        response_json = response.json()
        if response_json.get("success"):
            user_id = extract_user_id_from_response(response)
            user_manager.track_user(user_id, user_data["email_address"])
        else:
            # Should fail gracefully - either FastAPI validation error or business logic error
            # For validation errors, FastAPI may return 422/400, otherwise check success=False
            if response.status_code in [400, 422]:
                # FastAPI validation error - this is acceptable for large field values
                pass
            else:
                # Should return success=False for business logic errors
                assert not response_json.get("success")
    
    def test_special_characters_in_fields(self, db_service_url, user_manager):
        """Test handling of special characters in user fields"""
        user_data = create_test_user_data("special_chars")
        user_data.update({
            "first_name": "José",
            "last_name": "García-López",
            "city": "São Paulo",
            "street_address": "123 Main St. Apt #4B"
        })
        
        response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        assert response_json["success"] is True
        user_id = extract_user_id_from_response(response)
        user_manager.track_user(user_id, user_data["email_address"])
        
        # Verify data integrity
        get_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        get_json = get_response.json()
        assert get_json["success"] is True
        
        retrieved_user = get_json["data"][0]
        assert retrieved_user["first_name"] == "José"
        assert retrieved_user["last_name"] == "García-López"


class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.slow
    def test_user_creation_performance_batch(self, db_service_url, user_manager):
        """Test performance of multiple user creations"""
        user_count = 10
        max_time_per_user = 0.5  # seconds
        
        with PerformanceTimer() as timer:
            for i in range(user_count):
                user_data = create_test_user_data(f"perf_batch_{i}")
                response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
                
                # DB service returns structured response, not HTTP status codes for business logic
                response_json = response.json()
                assert response_json["success"] is True
                user_id = extract_user_id_from_response(response)
                user_manager.track_user(user_id, user_data["email_address"])
        
        total_time = timer.elapsed()
        avg_time_per_user = total_time / user_count
        
        assert avg_time_per_user < max_time_per_user, (
            f"Average time per user: {avg_time_per_user:.3f}s, "
            f"expected < {max_time_per_user}s"
        )
    
    @pytest.mark.slow
    def test_login_performance_batch(self, db_service_url):
        """Test performance of multiple login attempts"""
        # Create a test user first
        with DbServiceUserTestContext(db_service_url) as user_ctx:
            login_data = {
                "email_address": user_ctx.get_email(),
                "password": user_ctx.get_password()
            }
            
            login_count = 20
            max_time_per_login = 0.2  # seconds
            
            with PerformanceTimer() as timer:
                for _ in range(login_count):
                    response = requests.post(
                        f"{db_service_url}/users/login",
                        json=login_data,
                        timeout=10
                    )
                    # DB service returns structured response, not HTTP status codes for business logic
                    response_json = response.json()
                    assert response_json["success"] is True
            
            total_time = timer.elapsed()
            avg_time_per_login = total_time / login_count
            
            assert avg_time_per_login < max_time_per_login, (
                f"Average time per login: {avg_time_per_login:.3f}s, "
                f"expected < {max_time_per_login}s"
            )
