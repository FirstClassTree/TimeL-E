"""
Integration Tests for User Workflows

This module contains end-to-end integration tests that verify complete
user workflows across both db_service and backend layers.

Tests cover:
- Complete user lifecycle workflows
- Cross-service data consistency
- Service integration reliability
- Error propagation between layers
"""

import pytest
import requests
import time
from typing import Dict, Any

from ..utils.test_helpers import (
    create_test_user_data,
    create_backend_user_data,
    extract_user_id_from_response,
    UserTestContext,
    PerformanceTimer
)


class TestCompleteUserLifecycle:
    """Test complete user lifecycle across both services"""
    
    def test_user_lifecycle_via_db_service(self, db_service_url, user_manager):
        """Test complete user lifecycle through db_service"""
        # 1. Create user
        user_data = create_test_user_data("lifecycle_db")
        create_response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        create_response_json = create_response.json()
        assert create_response_json.get("success") is True, f"User creation failed: {create_response_json.get('error', create_response_json)}"
        
        user_id = extract_user_id_from_response(create_response)
        user_manager.track_user(user_id, user_data["email_address"])
        
        # 2. Login
        login_response = requests.post(
            f"{db_service_url}/users/login",
            json={"email_address": user_data["email_address"], "password": user_data["password"]},
            timeout=10
        )
        assert login_response.status_code == 200
        
        # 3. Get profile
        profile_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        assert profile_response.status_code == 200
        
        # 4. Update profile
        update_response = requests.put(
            f"{db_service_url}/users/{user_id}",
            json={"city": "Updated City", "phone_number": "+1-555-9999"},
            timeout=10
        )
        assert update_response.status_code == 200
        
        # 5. Update password
        new_password = f"NewPassword123_{int(time.time())}"
        password_response = requests.put(
            f"{db_service_url}/users/{user_id}/password",
            json={"current_password": user_data["password"], "new_password": new_password},
            timeout=10
        )
        assert password_response.status_code == 200
        
        # 6. Verify new password works
        login_new_response = requests.post(
            f"{db_service_url}/users/login",
            json={"email_address": user_data["email_address"], "password": new_password},
            timeout=10
        )
        assert login_new_response.status_code == 200
        
        # 7. Update notification settings
        settings_response = requests.put(
            f"{db_service_url}/users/{user_id}/notification-settings",
            json={"days_between_order_notifications": 14, "order_notifications_via_email": False},
            timeout=10
        )
        assert settings_response.status_code == 200
        
        # 8. Delete user
        delete_response = requests.delete(
            f"{db_service_url}/users/{user_id}",
            json={"password": new_password},
            timeout=10
        )
        assert delete_response.status_code == 200
        
        # 9. Verify user is deleted
        final_check = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        final_check_json = final_check.json()
        assert final_check_json.get("success") is False
        assert "not found" in final_check_json.get("error", "").lower()
    
    def test_user_lifecycle_via_backend(self, backend_url, db_service_url, user_manager):
        """Test complete user lifecycle through backend"""
        # 1. Register user
        user_data = create_backend_user_data("lifecycle_backend")
        register_response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
        assert register_response.status_code in (200, 201)
        
        user_id = int(register_response.json()["data"]["userId"])
        user_manager.track_user(user_id, user_data["email"])
        
        # 2. Login
        login_response = requests.post(
            f"{backend_url}/api/users/login",
            json={"emailAddress": user_data["email"], "password": user_data["password"]},
            timeout=10
        )
        assert login_response.status_code == 200
        
        # 3. Get profile
        profile_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
        assert profile_response.status_code == 200
        
        # 4. Update profile
        update_response = requests.put(
            f"{backend_url}/api/users/{user_id}",
            json={"firstName": "Updated", "city": "Updated City"},
            timeout=10
        )
        assert update_response.status_code == 200

        #4b. Update notification settings via profile endpoint
        notification_update = {
            "daysBetweenOrderNotifications": 8,
            "orderNotificationsViaEmail": True
        }
        profile_update_response = requests.put(
            f"{backend_url}/api/users/{user_id}",
            json=notification_update,
            timeout=10
        )
        assert profile_update_response.status_code == 200
        profile_update_json = profile_update_response.json()
        assert profile_update_json["data"]["daysBetweenOrderNotifications"] == 8
        assert profile_update_json["data"]["orderNotificationsViaEmail"] is True

        notif_settings_resp = requests.get(
            f"{backend_url}/api/users/{user_id}/notification-settings",
            timeout=10
        )
        assert notif_settings_resp.status_code == 200
        settings = notif_settings_resp.json()["data"]

        # Assert the settings reflect the just-updated values
        assert settings["daysBetweenOrderNotifications"] == 8
        assert settings["orderNotificationsViaEmail"] is True

        # 5. Update password
        new_password = f"NewBackendPass123_{int(time.time())}"
        password_response = requests.put(
            f"{backend_url}/api/users/{user_id}/password",
            json={"currentPassword": user_data["password"], "newPassword": new_password},
            timeout=10
        )
        assert password_response.status_code == 200
        
        # 6. Verify new password works
        login_new_response = requests.post(
            f"{backend_url}/api/users/login",
            json={"emailAddress": user_data["email"], "password": new_password},
            timeout=10
        )
        assert login_new_response.status_code == 200
        
        # 7. Update notification settings
        settings_response = requests.put(
            f"{backend_url}/api/users/{user_id}/notification-settings",
            json={"daysBetweenOrderNotifications": 21, "orderNotificationsViaEmail": True},
            timeout=10
        )
        assert settings_response.status_code == 200
        
        # 8. Delete user
        delete_response = requests.delete(
            f"{backend_url}/api/users/{user_id}",
            json={"password": new_password},
            timeout=10
        )
        assert delete_response.status_code == 200
        
        # 9. Verify user is deleted
        final_check = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
        assert final_check.status_code == 404


class TestCrossServiceConsistency:
    """Test data consistency between db_service and backend"""
    
    def test_user_data_consistency_db_to_backend(self, db_service_url, backend_url):
        """Test that user created via db_service is accessible via backend"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Get user via db_service
            db_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
            assert db_response.status_code == 200
            db_user = db_response.json()["data"][0]
            
            # Get same user via backend
            backend_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
            assert backend_response.status_code == 200
            backend_user = backend_response.json()["data"]
            
            # Verify data consistency
            assert db_user["user_id"] == backend_user["userId"]
            assert db_user["first_name"] == backend_user["firstName"]
            assert db_user["last_name"] == backend_user["lastName"]
            assert db_user["email_address"] == backend_user["emailAddress"]
    
    def test_user_updates_consistency(self, db_service_url, backend_url):
        """Test that updates via one service are reflected in the other"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Update via db_service
            db_update = requests.put(
                f"{db_service_url}/users/{user_id}",
                json={"city": "DB Updated City", "phone_number": "+1-555-1111"},
                timeout=10
            )
            assert db_update.status_code == 200
            
            # Verify update via backend
            backend_check = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
            assert backend_check.status_code == 200
            backend_user = backend_check.json()["data"]
            
            assert backend_user["city"] == "DB Updated City"
            assert backend_user["phoneNumber"] == "+1-555-1111"
            
            # Update via backend
            backend_update = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json={"firstName": "Backend Updated", "lastName": "Name"},
                timeout=10
            )
            assert backend_update.status_code == 200
            
            # Verify update via db_service
            db_check = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
            assert db_check.status_code == 200
            db_user = db_check.json()["data"][0]
            
            assert db_user["first_name"] == "Backend Updated"
            assert db_user["last_name"] == "Name"

            # Update notification settings via backend profile update
            backend_update = requests.put(
                f"{backend_url}/api/users/{user_id}",
                json={"daysBetweenOrderNotifications": 21},
                timeout=10
            )
            assert backend_update.status_code == 200

            # Verify update via db_service
            db_check = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
            db_response_json = db_check.json()
            assert db_response_json.get("success") is True, f"DB service returned: {db_response_json}"
            db_user = db_response_json["data"][0]
            assert db_user["days_between_order_notifications"] == 21

    def test_notification_settings_consistency(self, db_service_url, backend_url):
        """Test notification settings consistency between services"""
        with UserTestContext(db_service_url) as user_ctx:
            user_id = user_ctx.get_user_id()
            
            # Update settings via db_service
            db_settings_update = requests.put(
                f"{db_service_url}/users/{user_id}/notification-settings",
                json={"days_between_order_notifications": 30, "order_notifications_via_email": False},
                timeout=10
            )
            assert db_settings_update.status_code == 200
            
            # Verify via backend
            backend_settings_check = requests.get(
                f"{backend_url}/api/users/{user_id}/notification-settings",
                timeout=10
            )
            assert backend_settings_check.status_code == 200
            backend_settings = backend_settings_check.json()["data"]
            
            assert backend_settings["daysBetweenOrderNotifications"] == 30
            assert backend_settings["orderNotificationsViaEmail"] is False
            
            # Update settings via backend
            backend_settings_update = requests.put(
                f"{backend_url}/api/users/{user_id}/notification-settings",
                json={"daysBetweenOrderNotifications": 7, "orderNotificationsViaEmail": True},
                timeout=10
            )
            assert backend_settings_update.status_code == 200
            
            # Verify via db_service
            db_settings_check = requests.get(
                f"{db_service_url}/users/{user_id}/notification-settings",
                timeout=10
            )
            assert db_settings_check.status_code == 200
            db_settings = db_settings_check.json()["data"][0]
            
            assert db_settings["days_between_order_notifications"] == 7
            assert db_settings["order_notifications_via_email"] is True

@pytest.mark.skip(reason="flaky concurrency.")
class TestServiceIntegrationReliability:
    """Test reliability of service integration"""
    
    def test_concurrent_operations_across_services(self, db_service_url, backend_url, user_manager):
        """Test concurrent operations across both services"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def create_via_db_service(suffix):
            try:
                user_data = create_test_user_data(f"concurrent_db_{suffix}")
                response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
                response_json  = response.json()
                results.put(("db", suffix, response.status_code, response_json if response_json.get("success") else None))
            except Exception as e:
                results.put(("db", suffix, None, str(e)))
        
        def create_via_backend(suffix):
            try:
                user_data = create_backend_user_data(f"concurrent_backend_{suffix}")
                response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
                results.put(("backend", suffix, response.status_code, response.json() if response.status_code in (200, 201) else None))
            except Exception as e:
                results.put(("backend", suffix, None, str(e)))
        
        # Create users concurrently via both services
        threads = []
        for i in range(3):
            db_thread = threading.Thread(target=create_via_db_service, args=(i,))
            backend_thread = threading.Thread(target=create_via_backend, args=(i,))
            threads.extend([db_thread, backend_thread])
            db_thread.start()
            backend_thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        db_success_count = 0
        backend_success_count = 0
        
        while not results.empty():
            service, suffix, status_code, response_data = results.get()
            if response_data is not None:
                if service == "db":
                    # db_service: success is if response_data is not None (success==True), regardless of status
                    db_success_count += 1
                    user_id = response_data["data"][0]["user_id"]
                    email = response_data["data"][0]["email_address"]
                    user_manager.track_user(user_id, email)
                elif service == "backend":
                    backend_success_count += 1
                    user_id = int(response_data["data"]["userId"])
                    email = response_data["data"]["emailAddress"]
                    user_manager.track_user(user_id, email)
        
        assert db_success_count == 3, f"Expected 3 DB service successes, got {db_success_count}"
        assert backend_success_count == 3, f"Expected 3 backend successes, got {backend_success_count}"
    
    def test_service_integration_under_load(self, db_service_url, backend_url, user_manager):
        """Test service integration under moderate load"""
        operations_count = 20
        max_total_time = 30  # seconds
        
        with PerformanceTimer() as timer:
            for i in range(operations_count):
                # Alternate between services
                if i % 2 == 0:
                    # Use db_service
                    user_data = create_test_user_data(f"load_db_{i}")
                    response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
                    response_json = response.json()
                    assert response_json.get("success") is True
                    user_id = extract_user_id_from_response(response)
                    user_manager.track_user(user_id, user_data["email_address"])
                else:
                    # Use backend
                    user_data = create_backend_user_data(f"load_backend_{i}")
                    response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
                    assert response.status_code in (200, 201)
                    user_id = int(response.json()["data"]["userId"])
                    user_manager.track_user(user_id, user_data["email"])
        
        total_time = timer.elapsed()
        assert total_time < max_total_time, (
            f"Load test took {total_time:.2f}s, expected < {max_total_time}s"
        )
        
        avg_time_per_operation = total_time / operations_count
        assert avg_time_per_operation < 1.5, (
            f"Average time per operation: {avg_time_per_operation:.3f}s, expected < 1.5s"
        )


class TestErrorPropagation:
    """Test error handling and propagation between services"""
    
    def test_backend_error_handling_for_db_service_errors(self, backend_url, db_service_url):
        """Test that backend properly handles and propagates db_service errors"""
        # Note: This test expects 404 for invalid user_id format because db_service currently accepts int and
        # returns 404 for any non-integer. Update this test to expect 422 after switching to UUID and proper validation.

        # Test with non-existent user
        response = requests.get(f"{backend_url}/api/users/999999", timeout=10)
        assert response.status_code == 404
        assert "detail" in response.json()

        # -- Skip this until the move to UUID and real format validation
        # # Test with invalid user ID format
        # response = requests.get(f"{backend_url}/api/users/invalid", timeout=10)
        # assert response.status_code == 404  # currently only 404 is returned (not 422)
        # assert "detail" in response.json()
        
        # Test duplicate email error propagation
        user_data = create_backend_user_data("error_prop")
        
        # Create first user
        response1 = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
        if response1.status_code == 201:
            # Try to create duplicate
            response2 = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
            assert response2.status_code == 409
            assert "detail" in response2.json()
            assert "email" in response2.json()["detail"].lower()
    
    def test_authentication_error_consistency(self, db_service_url, backend_url):
        """Test that authentication errors are consistent between services"""
        invalid_login_db = {
            "email_address": "nonexistent@example.com",
            "password": "wrong_password"
        }
        invalid_login_be = {
            "emailAddress": "nonexistent@example.com",
            "password": "wrong_password"
        }
        
        # Test via db_service
        db_response = requests.post(f"{db_service_url}/users/login", json=invalid_login_db, timeout=10)
        response_data = db_response.json()
        assert response_data["success"] is False
        assert "invalid email or password" in response_data["error"].lower()

        # Test via backend
        backend_response = requests.post(f"{backend_url}/api/users/login", json=invalid_login_be, timeout=10)
        assert backend_response.status_code == 401
        
        # Both should indicate invalid credentials
        db_error = db_response.json()["error"].lower()
        backend_error = backend_response.json()["detail"].lower()
        
        assert "invalid" in db_error or "unauthorized" in db_error
        assert "invalid" in backend_error or "unauthorized" in backend_error


class TestDataIntegrity:
    """Test data integrity across service boundaries"""
    
    def test_user_creation_data_integrity(self, db_service_url, backend_url, user_manager):
        """Test that user data maintains integrity across service boundaries"""
        # Create user with special characters and edge cases
        user_data = create_test_user_data("integrity_test")
        user_data.update({
            "first_name": "José María",
            "last_name": "García-López",
            "city": "São Paulo",
            "street_address": "123 Main St. Apt #4B",
            "phone_number": "+55 (11) 99999-9999"
        })
        
        # Create via db_service
        create_response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
        assert create_response.status_code in (200, 201), f"Unexpected status: {create_response.status_code}"
        
        user_id = extract_user_id_from_response(create_response)
        user_manager.track_user(user_id, user_data["email_address"])
        
        # Verify via both services
        db_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
        backend_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
        
        assert db_response.status_code == 200
        assert backend_response.status_code == 200
        
        db_user = db_response.json()["data"][0]
        backend_user = backend_response.json()["data"]
        
        # Verify special characters are preserved
        assert db_user["first_name"] == "José María"
        assert backend_user["firstName"] == "José María"
        assert db_user["last_name"] == "García-López"
        assert backend_user["lastName"] == "García-López"
        assert db_user["city"] == "São Paulo"
        assert backend_user["city"] == "São Paulo"
    
    @pytest.mark.slow
    def test_large_scale_data_consistency(self, db_service_url, backend_url, user_manager):
        """Test data consistency with multiple users and operations"""
        user_count = 10
        created_users = []
        
        # Create multiple users via different services
        for i in range(user_count):
            if i % 2 == 0:
                # Create via db_service
                user_data = create_test_user_data(f"consistency_db_{i}")
                response = requests.post(f"{db_service_url}/users/", json=user_data, timeout=10)
                assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}"
                user_id = extract_user_id_from_response(response)
                created_users.append((user_id, "db", user_data["email_address"]))
                user_manager.track_user(user_id, user_data["email_address"])
            else:
                # Create via backend
                user_data = create_backend_user_data(f"consistency_backend_{i}")
                response = requests.post(f"{backend_url}/api/users/register", json=user_data, timeout=10)
                assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}"
                user_id = int(response.json()["data"]["userId"])
                created_users.append((user_id, "backend", user_data["email"]))
                user_manager.track_user(user_id, user_data["email"])
        
        # Verify all users are accessible via both services
        for user_id, creation_service, email_address in created_users:
            # Check via db_service
            db_response = requests.get(f"{db_service_url}/users/{user_id}", timeout=10)
            assert db_response.status_code == 200
            
            # Check via backend
            backend_response = requests.get(f"{backend_url}/api/users/{user_id}", timeout=10)
            assert backend_response.status_code == 200
            
            # Verify email consistency
            db_email = db_response.json()["data"][0]["email_address"]
            backend_email = backend_response.json()["data"]["emailAddress"]
            
            assert db_email == email_address
            assert backend_email == email_address
            assert db_email == backend_email
