"""
Backend User API Tests

This module contains comprehensive tests for the backend user routes,
testing them through the backend → db_service integration layer.

Tests cover:
- User registration and management via backend
- Authentication through backend
- Profile management via backend
- Error handling and HTTP status mapping
- Service integration reliability
"""

import pytest
import requests
import time
from datetime import datetime, UTC
from typing import Dict, Any

from ..utils.test_helpers import (
    create_backend_user_data,
    create_test_user_data,
    create_invalid_user_data,
    create_notification_settings_data,
    extract_user_id_from_response,
    extract_user_email_from_response,
    assert_datetime_close,
    assert_user_data_matches,
    assert_response_has_structure,
    cleanup_test_user,
    UserTestContext,
    PerformanceTimer,
    measure_response_time
)

OPTIONAL_USER_FIELDS = [
    "phoneNumber",
    "streetAddress",
    "city",
    "postalCode",
    "country",
    "daysBetweenOrderNotifications",
    "orderNotificationsStartDateTime",
    "orderNotificationsNextScheduledTime",
    "pendingOrderNotification",
    "orderNotificationsViaEmail",
    "lastNotificationSentAt"
]
OPTIONAL_NOTIFICATION_SETTINGS_FIELDS = [
    "daysBetweenOrderNotifications",
    "orderNotificationsStartDateTime",
    "orderNotificationsNextScheduledTime",
    "orderNotificationsViaEmail",
    "pendingOrderNotification",
    "lastNotificationSentAt"
]

class TestBackendUserRegistration:
    """Test user registration through backend API"""

    def test_register_user_success(self, backend_url, db_service_url, user_manager):
        """Test successful user registration via backend"""
        user_data = create_backend_user_data("backend_register")

        response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)

        assert response.status_code in (200, 201), f"Expected 201, got {response.status_code}: {response.text}"

        response_json = response.json()
        assert "message" in response_json
        assert "data" in response_json

        created_user = response_json["data"]
        user_id = created_user["userId"]

        # Track for cleanup via db_service
        user_manager.track_user(int(user_id), created_user["emailAddress"])

        # Validate response structure (backend format)
        assert_response_has_structure(
            created_user,
            required_fields=["userId", "firstName", "lastName", "emailAddress"],
            optional_fields=OPTIONAL_USER_FIELDS,
            forbidden_fields=["password", "hashedPassword"]
        )

        # Validate data matches (accounting for field name differences)
        assert created_user["firstName"] == user_data["firstName"]
        assert created_user["lastName"] == user_data["lastName"]
        assert created_user["emailAddress"] == user_data["email"]

    def test_register_user_minimal_fields(self, backend_url, db_service_url, user_manager):
        """Test user registration with minimal required fields"""
        user_data = create_backend_user_data("backend_minimal", include_optional=False)

        response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)

        assert response.status_code in (200, 201)
        response_json = response.json()
        
        created_user = response_json["data"]
        user_id = int(created_user["userId"])
        
        user_manager.track_user(user_id, created_user["emailAddress"])

        assert_response_has_structure(
            created_user,
            required_fields=["userId", "firstName", "lastName", "emailAddress"],
            optional_fields=OPTIONAL_USER_FIELDS,
            forbidden_fields=["password", "hashedPassword"]
        )

        # Check required fields are present
        assert created_user["firstName"] == user_data["firstName"]
        assert created_user["lastName"] == user_data["lastName"]
        assert created_user["emailAddress"] == user_data["email"]
    
    def test_register_user_duplicate_email(self, backend_url, db_service_url, user_manager):
        """Test user registration with duplicate email via backend"""
        user_data = create_backend_user_data("backend_duplicate")
        
        # Create first user
        response1 = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
        assert response1.status_code in (200, 201)
        
        user_id = int(response1.json()["data"]["userId"])
        user_manager.track_user(user_id, user_data["email"])
        
        # Try to create second user with same email
        user_data2 = create_backend_user_data("backend_duplicate2")
        user_data2["email"] = user_data["email"]  # Same email
        
        response2 = requests.post(f"{backend_url}/api/users/register", json=user_data2, timeout=10)
        
        assert response2.status_code == 409
        response_json = response2.json()
        assert "detail" in response_json
        assert "email" in response_json["detail"].lower()
    
    def test_register_user_invalid_data(self, backend_url):
        """Test user registration with invalid data via backend"""
        invalid_data = {
            "firstName": "",  # Empty required field
            "lastName": "",   # Empty required field
            "email": "invalid-email-format",  # Invalid email
            "password": "123"  # Too short
        }
        
        response = requests.post(f"{backend_url}/api/users/register", json=invalid_data, timeout=10)
        
        assert response.status_code == 422 or response.status_code == 400
        response_json = response.json()
        assert "detail" in response_json
    
    def test_register_user_missing_required_fields(self, backend_url):
        """Test user registration with missing required fields"""
        incomplete_data = {
            "firstName": "Test"
            # Missing lastName, email, password
        }
        
        response = requests.post(f"{backend_url}/api/users/register", json=incomplete_data, timeout=10)
        
        assert response.status_code == 422
        response_json = response.json()
        assert "detail" in response_json


class TestBackendUserAuthentication:
    """Test user authentication through backend API"""
    
    def test_demo_login(self, backend_url):
        """Test demo login functionality"""
        response = requests.get(f"{backend_url}/api/users/login", timeout=10)
        
        assert response.status_code == 200
        response_json = response.json()
        
        assert "message" in response_json
        assert "data" in response_json
        
        user_data = response_json["data"]
        assert "userId" in user_data
        assert "demoUser" in user_data
        assert user_data["demoUser"] is True
        assert "mlPredictionsAvailable" in user_data
    
    def test_real_login_success(self, backend_url, db_service_url):
        """Test real user login via backend"""
        # Create user via db_service first
        with UserTestContext(db_service_url) as user_ctx:
            login_data = {
                "emailAddress": user_ctx.get_email(),
                "password": user_ctx.get_password()
            }
            
            response = requests.post(f"{backend_url}/api/users/login", json=login_data, timeout=10)
            
            assert response.status_code == 200
            response_json = response.json()
            
            assert "message" in response_json
            assert "data" in response_json
            
            user_data = response_json["data"]
            assert user_data["userId"] == user_ctx.get_user_id()
            assert user_data["emailAddress"] == user_ctx.get_email()
    
    def test_login_invalid_credentials(self, backend_url):
        """Test login with invalid credentials via backend"""
        login_data = {
            "emailAddress": "nonexistent@example.com",
            "password": "wrong_password"
        }
        
        response = requests.post(f"{backend_url}/api/users/login", json=login_data, timeout=10)
        
        assert response.status_code == 401
        response_json = response.json()
        assert "detail" in response_json
        assert "invalid" in response_json["detail"].lower()
    
    def test_login_malformed_request(self, backend_url):
        """Test login with malformed request via backend"""
        login_data = {
            "email": "missing_address_field@example.com"
            # Missing password
        }
        
        response = requests.post(f"{backend_url}/api/users/login", json=login_data, timeout=10)
        
        assert response.status_code == 422


class TestBackendUserProfile:
    """Test user profile management through backend API"""
    
    def test_get_user_profile_success(self, backend_url, db_service_url):
        """Test successful user profile retrieval via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
            
            assert response.status_code == 200
            response_json = response.json()
            
            assert "message" in response_json
            assert "data" in response_json
            
            user_data = response_json["data"]
            assert user_data["userId"] == user_id
            assert user_data["emailAddress"] == user_ctx.get_email()
            
            # Ensure sensitive data is not returned
            assert_response_has_structure(
                user_data,
                required_fields=["userId", "firstName", "lastName", "emailAddress"],
                optional_fields=OPTIONAL_USER_FIELDS,
                forbidden_fields=["password", "hashedPassword"]
            )
    
    def test_get_user_profile_not_found(self, backend_url):
        """Test profile retrieval for non-existent user via backend"""
        non_existent_id = 999999
        
        response = requests.get(f"{backend_url}/api/users/{non_existent_id}", timeout=10)
        
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json
        assert "not found" in response_json["detail"].lower()
    
    def test_update_user_profile_success(self, backend_url, db_service_url):
        """Test successful user profile update via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "firstName": "Updated",
                "lastName": "Name",
                "phone": "+1-555-9999",
                "city": "Updated City",
                "daysBetweenOrderNotifications": 11,
                "orderNotificationsViaEmail": True
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 200
            response_json = response.json()
            
            assert "message" in response_json
            assert "data" in response_json
            
            updated_user = response_json["data"]
            assert updated_user["firstName"] == update_data["firstName"]
            assert updated_user["lastName"] == update_data["lastName"]
            assert updated_user["phoneNumber"] == update_data["phone"]
            assert updated_user["city"] == update_data["city"]
            assert updated_user["daysBetweenOrderNotifications"] == 11
            assert updated_user["orderNotificationsViaEmail"] is True

    def test_update_user_profile_invalid_notification_fields(self, backend_url, db_service_url):
        """Test updating profile with invalid notification field values"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            bad_update = {
                "daysBetweenOrderNotifications": 999  # Invalid (> 365)
            }
            response = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json=bad_update,
                timeout=10
            )
            assert response.status_code == 400, f"Expected 400/422, got {response.status_code}: {response.text}"
            error_msg = response.json().get("detail") or response.json().get("error", "")
            assert "between 1 and 365" in error_msg.lower()

    def test_update_user_profile_with_notification_fields(self, backend_url, db_service_url):
        """Test updating notification fields via profile update endpoint"""
        from datetime import datetime, UTC, timedelta
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            # Pick notification fields
            update_data = {
                "daysBetweenOrderNotifications": 17,
                "orderNotificationsViaEmail": True,
                "orderNotificationsStartDateTime": (datetime.now(UTC) + timedelta(days=1)).isoformat()
            }

            response = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json=update_data,
                timeout=10
            )
            assert response.status_code == 200, f"Status: {response.status_code}, Body: {response.text}"
            response_json = response.json()
            assert "data" in response_json
            updated_user = response_json["data"]

            assert updated_user["daysBetweenOrderNotifications"] == 17
            assert updated_user["orderNotificationsViaEmail"] is True
            assert updated_user["orderNotificationsStartDateTime"].startswith(
                update_data["orderNotificationsStartDateTime"][:16])  # ISO format check

            # Sanity: downstream notification settings GET should reflect changes
            notif_settings = requests.get(
                f"{backend_url}/api/users/{user_id}/notification-settings", timeout=10).json()["data"]
            assert notif_settings["daysBetweenOrderNotifications"] == 17
            assert notif_settings["orderNotificationsViaEmail"] is True
            assert updated_user["orderNotificationsStartDateTime"].startswith(
                update_data["orderNotificationsStartDateTime"][:16])  # ISO format check

    def test_update_user_profile_not_found(self, backend_url):
        """Test profile update for non-existent user via backend"""
        non_existent_id = 999999
        update_data = {"firstName": "Updated"}
        
        response = requests.put(
            f"{backend_url}/api/users/{non_existent_id}",
            json=update_data,
            timeout=10
        )
        
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json
    
    def test_update_user_profile_no_fields(self, backend_url, db_service_url):
        """Test profile update with no fields via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json={},
                timeout=10
            )
            
            assert response.status_code == 400
            response_json = response.json()
            assert "detail" in response_json
            assert "no fields" in response_json["detail"].lower()


class TestBackendUserDeletion:
    """Test user deletion through backend API"""
    
    def test_delete_user_success(self, backend_url, db_service_url):
        """Test successful user deletion via backend"""
        # Create user via db_service
        user_data = create_test_user_data("backend_delete")
        create_response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        assert create_response.status_code in (200, 201), f"Unexpected status: {create_response.status_code}"
        
        user_id = extract_user_id_from_response(create_response)
        
        # Delete via backend
        delete_data = {"password": user_data["password"]}
        delete_response = requests.delete(
            f"{backend_url}/api/users/{user_id}",
            json=delete_data,
            timeout=10
        )

        assert delete_response.status_code == 200
        response_json = delete_response.json()
        assert "message" in response_json
        assert "data" in response_json
        
        # Verify user is deleted
        get_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
        assert get_response.status_code == 404
    
    def test_delete_user_wrong_password(self, backend_url, db_service_url):
        """Test user deletion with wrong password via backend"""
        with UserTestContext(db_service_url, auto_cleanup=False) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            delete_data = {"password": "wrong_password"}
            response = requests.delete(
                f"{backend_url}/api/users/{user_id}",
                json=delete_data,
                timeout=10
            )
            
            assert response.status_code == 400
            response_json = response.json()
            assert "detail" in response_json
            assert "password" in response_json["detail"].lower()
    
    def test_delete_user_not_found(self, backend_url):
        """Test deletion of non-existent user via backend"""
        non_existent_id = 999999
        delete_data = {"password": "any_password"}
        
        response = requests.delete(
            f"{backend_url}/api/users/{non_existent_id}",
            json=delete_data,
            timeout=10
        )
        
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json


class TestBackendPasswordManagement:
    """Test password management through backend API"""
    
    def test_update_password_success(self, backend_url, db_service_url):
        """Test successful password update via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            current_password = user_ctx.get_password()
            new_password = "NewBackendPass123_" + str(int(time.time()))
            
            update_data = {
                "currentPassword": current_password,
                "newPassword": new_password
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/password",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 200
            response_json = response.json()
            assert "message" in response_json
            assert "data" in response_json
            
            # Verify new password works via backend login
            login_data = {
                "emailAddress": user_ctx.get_email(),
                "password": new_password
            }
            
            login_response = requests.post(
                f"{backend_url}/api/users/login",
                json=login_data,
                timeout=10
            )
            
            assert login_response.status_code == 200
    
    def test_update_password_wrong_current(self, backend_url, db_service_url):
        """Test password update with wrong current password via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "currentPassword": "wrong_password",
                "newPassword": "NewPassword123"
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/password",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 400
            response_json = response.json()
            assert "detail" in response_json
            assert "current password" in response_json["detail"].lower()
    
    def test_update_password_user_not_found(self, backend_url):
        """Test password update for non-existent user via backend"""
        non_existent_id = 999999
        update_data = {
            "currentPassword": "any_password",
            "newPassword": "NewPassword123"
        }
        
        response = requests.put(
            f"{backend_url}/api/users/{non_existent_id}/password",
            json=update_data,
            timeout=10
        )
        
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json


class TestBackendEmailManagement:
    """Test email management through backend API"""
    
    def test_update_email_success(self, backend_url, db_service_url):
        """Test successful email update via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            current_password = user_ctx.get_password()
            new_email = f"backend_updated_{int(time.time())}@timele-test.com"
            
            update_data = {
                "currentPassword": current_password,
                "newEmailAddress": new_email
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/email",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 200
            response_json = response.json()
            assert "message" in response_json
            assert "data" in response_json
            
            # Verify new email works for login via backend
            login_data = {
                "emailAddress": new_email,
                "password": current_password
            }
            
            login_response = requests.post(
                f"{backend_url}/api/users/login",
                json=login_data,
                timeout=10
            )
            
            assert login_response.status_code == 200
    
    def test_update_email_duplicate(self, backend_url, db_service_url):
        """Test email update to existing email via backend"""
        # Create two users via db_service
        with UserTestContext(db_service_url) as user1_ctx:
            with UserTestContext(db_service_url) as user2_ctx:
                user1_id = user1_ctx.get_user_id()
                user1_password = user1_ctx.get_password()
                user2_email = user2_ctx.get_email()
                
                # Try to update user1's email to user2's email via backend
                update_data = {
                    "currentPassword": user1_password,
                    "newEmailAddress": user2_email
                }
                
                response = requests.put(
                    f"{backend_url}/api/users/{user1_id}/email",
                    json=update_data,
                    timeout=10
                )
                
                assert response.status_code == 409
                response_json = response.json()
                assert "detail" in response_json
                assert "email" in response_json["detail"].lower()
    
    def test_update_email_wrong_password(self, backend_url, db_service_url):
        """Test email update with wrong password via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            new_email = f"backend_new_{int(time.time())}@timele-test.com"
            
            update_data = {
                "currentPassword": "wrong_password",
                "newEmailAddress": new_email
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/email",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 400
            response_json = response.json()
            assert "detail" in response_json
            assert "password" in response_json["detail"].lower()

class TestBackendNotificationSettings:
    """Test notification settings through backend API"""
    
    def test_get_notification_settings(self, backend_url, db_service_url):
        """Test retrieval of notification settings via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            response = requests.get(
                f"{backend_url}/api/users/{user_id}/notification-settings",
                timeout=10
            )
            
            assert response.status_code == 200
            response_json = response.json()
            
            assert "message" in response_json
            assert "data" in response_json
            
            settings = response_json["data"]
            assert_response_has_structure(
                settings,
                required_fields=["userId"],
                optional_fields=OPTIONAL_NOTIFICATION_SETTINGS_FIELDS
            )
    
    def test_update_notification_settings_success(self, backend_url, db_service_url):
        """Test notification settings update via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "daysBetweenOrderNotifications": 14,
                "orderNotificationsViaEmail": False
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 200
            response_json = response.json()
            
            assert "message" in response_json
            assert "data" in response_json
            
            settings = response_json["data"]

            assert_response_has_structure(
                settings,
                required_fields=["userId"],
                optional_fields=OPTIONAL_NOTIFICATION_SETTINGS_FIELDS
            )

            assert settings["daysBetweenOrderNotifications"] == 14
            assert settings["orderNotificationsViaEmail"] is False
    
    def test_update_notification_settings_invalid_range(self, backend_url, db_service_url):
        """Test notification settings update with invalid range via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            update_data = {
                "daysBetweenOrderNotifications": 500  # > 365
            }
            
            response = requests.put(
                f"{backend_url}/api/users/{user_id}/notification-settings",
                json=update_data,
                timeout=10
            )
            
            assert response.status_code == 400
            response_json = response.json()
            assert "detail" in response_json
    
    def test_notification_settings_user_not_found(self, backend_url):
        """Test notification settings for non-existent user via backend"""
        non_existent_id = 999999
        
        response = requests.get(
            f"{backend_url}/api/users/{non_existent_id}/notification-settings",
            timeout=10
        )
        
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json


class TestBackendErrorHandling:
    """Test error handling and HTTP status mapping"""
    
    def test_service_unavailable_simulation(self, backend_url):
        """Test backend behavior when db_service is unavailable"""
        # This test would require stopping db_service or using a mock
        # For now, we test with an invalid user ID that should trigger service errors
        invalid_id = "invalid_format"
        
        response = requests.get(f"{backend_url}/api/users/{invalid_id}", timeout=10)
        
        # Should get a proper HTTP error response
        assert response.status_code in [400, 422, 500]
        response_json = response.json()
        assert "detail" in response_json
    
    def test_malformed_json_request(self, backend_url):
        """Test backend handling of malformed JSON"""
        # Send invalid JSON
        response = requests.post(
            f"{backend_url}/api/users/register",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code == 422
        response_json = response.json()
        assert "detail" in response_json
    
    def test_missing_content_type(self, backend_url):
        """Test backend handling of missing content type"""
        user_data = create_backend_user_data("content_type_test")
        
        response = requests.post(
            f"{backend_url}/api/users/register",
            json=user_data,
            # Remove content-type header
            timeout=10
        )
        
        # Should still work as requests sets it automatically
        # But test that backend handles various content types gracefully
        assert response.status_code in [200, 201, 400, 422]
    
    def test_http_status_code_mapping(self, backend_url, db_service_url):
        """Test that backend properly maps db_service errors to HTTP status codes"""
        test_cases = [
            # (operation, expected_status, description)
            ("get_nonexistent_user", 404, "User not found"),
            ("invalid_user_id", 422, "Invalid user ID format"),
        ]
        
        for operation, expected_status, description in test_cases:
            response = None
            if operation == "get_nonexistent_user":
                response = requests.get(f"{backend_url}/api/users/999999", timeout=10)
            elif operation == "invalid_user_id":
                response = requests.get(f"{backend_url}/api/users/invalid", timeout=10)
            
            if response is not None:
                assert response.status_code == expected_status, (
                    f"{description}: expected {expected_status}, got {response.status_code}"
                )


class TestBackendPerformance:
    """Test backend performance and integration reliability"""
    
    @pytest.mark.slow
    def test_backend_registration_performance(self, backend_url, db_service_url, user_manager):
        """Test backend registration performance"""
        user_count = 5
        max_time_per_user = 1.0  # seconds (higher than direct db_service due to extra layer)
        
        with PerformanceTimer() as timer:
            for i in range(user_count):
                user_data = create_backend_user_data(f"backend_perf_{i}")
                response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
                
                assert response.status_code in (200, 201)
                user_id = int(response.json()["data"]["userId"])
                user_manager.track_user(user_id, user_data["email"])
        
        total_time = timer.elapsed()
        avg_time_per_user = total_time / user_count
        
        assert avg_time_per_user < max_time_per_user, (
            f"Average time per user: {avg_time_per_user:.3f}s, "
            f"expected < {max_time_per_user}s"
        )
    
    @pytest.mark.slow
    def test_backend_login_performance(self, backend_url, db_service_url):
        """Test backend login performance"""
        # Create a test user via db_service
        with UserTestContext(db_service_url) as user_ctx:
            login_data = {
                "emailAddress": user_ctx.get_email(),
                "password": user_ctx.get_password()
            }
            
            login_count = 10
            max_time_per_login = 0.5  # seconds
            
            with PerformanceTimer() as timer:
                for _ in range(login_count):
                    response = requests.post(
                        f"{backend_url}/api/users/login",
                        json=login_data,
                        timeout=10
                    )
                    assert response.status_code == 200
            
            total_time = timer.elapsed()
            avg_time_per_login = total_time / login_count
            
            assert avg_time_per_login < max_time_per_login, (
                f"Average time per login: {avg_time_per_login:.3f}s, "
                f"expected < {max_time_per_login}s"
            )
    
    def test_backend_service_integration_reliability(self, backend_url, db_service_url, user_manager):
        """Test reliability of backend → db_service integration"""
        # Perform multiple operations in sequence to test integration stability
        user_data = create_backend_user_data("integration_test")
        
        # 1. Register user
        register_response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
        assert register_response.status_code in (200, 201)
        register_response_json = register_response.json()
        assert "data" in register_response_json and "userId" in register_response_json["data"], f"Registration failed: {register_response_json}"
        
        user_id = int(register_response.json()["data"]["userId"])
        user_manager.track_user(user_id, user_data["email"])
        
        # 2. Login
        login_data = {
            "emailAddress": user_data["email"],
            "password": user_data["password"]
        }
        login_response = requests.post(f"{backend_url}/api/users/login", json=login_data, timeout=10)
        assert login_response.status_code == 200
        
        # 3. Get profile
        profile_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
        assert profile_response.status_code == 200
        
        # 4. Update profile
        update_data = {"firstName": "Updated", "city": "New City"}
        update_response = requests.put(f"{backend_url}/api/users/{user_id}", json=update_data, timeout=10)
        assert update_response.status_code == 200
        
        # 5. Get notification settings
        settings_response = requests.get(f"{backend_url}/api/users/{user_id}/notification-settings", timeout=10)
        assert settings_response.status_code == 200
        
        # 6. Update notification settings
        settings_update = {"daysBetweenOrderNotifications": 21}
        settings_update_response = requests.put(
            f"{backend_url}/api/users/{user_id}/notification-settings",
            json=settings_update,
            timeout=10
        )
        assert settings_update_response.status_code == 200
        
        # All operations should succeed, demonstrating reliable integration


class TestBackendFieldMapping:
    """Test field mapping between backend and db_service formats"""
    
    def test_registration_field_mapping(self, backend_url, db_service_url, user_manager):
        """Test that backend properly maps field names to db_service format"""
        backend_data = {
            "firstName": "Backend",
            "lastName": "User",
            "email": f"field_mapping_{int(time.time())}@timele-test.com",
            "password": "FieldMapping123",
            "phone": "+1-555-1234",
            "daysBetweenOrderNotifications": 10,
            "orderNotificationsViaEmail": True
        }
        
        response = requests.post(f"{backend_url}/api/users/register", json=backend_data, timeout=10)
        assert response.status_code in (200, 201)
        
        created_user = response.json()["data"]
        user_id = int(created_user["userId"])
        user_manager.track_user(user_id, backend_data["email"])
        
        # Verify field mapping worked correctly
        assert created_user["firstName"] == backend_data["firstName"]
        assert created_user["lastName"] == backend_data["lastName"]
        assert created_user["emailAddress"] == backend_data["email"]
        assert created_user["phoneNumber"] == backend_data["phone"]
        assert created_user["daysBetweenOrderNotifications"] == 10
        assert created_user["orderNotificationsViaEmail"] is True
        
        # Verify we can retrieve the user via db_service to confirm data integrity
        db_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        assert db_response.status_code == 200
        
        db_user = db_response.json()["data"][0]
        assert db_user["first_name"] == backend_data["firstName"]
        assert db_user["last_name"] == backend_data["lastName"]
        assert db_user["email_address"] == backend_data["email"]

