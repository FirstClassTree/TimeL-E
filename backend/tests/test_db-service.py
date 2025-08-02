import requests
import json
import random
import psycopg2
from datetime import datetime
import time
from dateutil.parser import parse as parse_datetime, parse as parse_datetime
# from uuid_utils import uuid7

def assert_db_success(json_resp, what="operation"):
    """
    Checks if db_service call was successful. Raises AssertionError if not, printing error field.
    Usage: assert_db_success(json_resp, "fetch products")
    """
    if not json_resp.get("success", False):
        error_msg = json_resp.get("error", "unknown error")
        raise AssertionError(f"Failed to {what}: {error_msg}")

def test_query():
    # Endpoint URL
    url = "http://localhost:7000/query"

    # The payload: use $1, $2 as parameter placeholders
    payload = {
        "sql": "SELECT * FROM products.products WHERE department_id = $1 LIMIT $2",
        "params": [19, 2]
    }
    # payload = {
    #     "sql": "SELECT * FROM products.products LIMIT $1",
    #     "params": [25]
    # }

    # Set headers
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # POST the request
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # # Raise error if response code is not 200
        # response.raise_for_status()

        json_resp = response.json()
        assert_db_success(json_resp, "query products")

        # Print the response in a pretty way
        print("Query data:", json.dumps(json_resp.get("data"), indent=2))



    except requests.RequestException as e:
        print("HTTP request failed:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Server response:", e.response.text)
    except Exception as e:
        print("General error:", e)

def test_get_products():
    url = "http://localhost:7000/products"
    params = {
        "limit": 5,
        "offset": 0,
        "categories": ["Bakery", "Dairy"]  # adjust as appropriate for your DB
    }
    response = requests.get(url, params=params)
    json_resp = response.json()
    assert_db_success(json_resp, "get products")
    print("\ntest_get_products:")
    print("Products:", json.dumps(json_resp.get("data"), indent=2))


CREATED_ORDER_ID = None
def test_create_order():
    global CREATED_ORDER_ID
    url = "http://localhost:7000/orders"
    payload = {
        # "user_id": "01981762-2cc0-740e-a010-df99a9bbc9d5",  # replace with a real user_id from DB
        "user_id": 86224,
        "order_dow": 3,
        "order_hour_of_day": 15,
        "total_items": 3,
        "items": [
            {"product_id": 101, "quantity": 2},
            {"product_id": 102, "quantity": 1}
        ]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print("\ntest_create_order:")
        response_json = response.json()
        assert_db_success(response_json, "create order")
        if response_json["success"]:
            print("Order created:", json.dumps(response_json.get("data"), indent=2))
            CREATED_ORDER_ID = (
                    response_json.get("order_id")
                    or response_json.get("id")
                    or (response_json.get("data", {}).get("order_id") if "data" in response_json else None)
            )
            print(f"Saved order_id: {CREATED_ORDER_ID}")
        else:
            print("Order creation error:", response_json.get("error", "unknown error"))
    except requests.RequestException as e:
        print("HTTP request failed:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Server response:", e.response.text)
    except Exception as e:
        print("General error:", e)
        test_create_order()


def test_orders_order_id_items():
    # order_id = "01981768-0d9d-723b-ac39-fd8fbdc2eadb"
    order_id = CREATED_ORDER_ID
    items = [
        {"product_id": 1, "quantity": 2},
        {"product_id": 5, "quantity": 1},
    ]

    resp = requests.post(
        f"http://localhost:7000/orders/{order_id}/items",
        json=items  # Items as list, not wrapped in a dict
    )
    json_resp = resp.json()
    assert_db_success(json_resp, "add items to order")
    print("\ntest_orders_order_id_items:")
    print("Added items:", json.dumps(json_resp.get("data"), indent=2))


# def test_delete_order():
#     # order_id = "01981768-0d9d-723b-ac39-fd8fbdc2eadb"
#     order_id = CREATED_ORDER_ID
#     items = [
#         {"product_id": 1, "quantity": 2},
#         {"product_id": 5, "quantity": 1},
#     ]
#
#     resp = requests.delete(f"http://localhost:7000/orders/{order_id}")
#
#     print("\ntest_delete_order:")
#     print(resp.status_code)
#     print(resp.json())

def test_enriched_products_across_departments():
    url = "http://localhost:7000/products"
    departments = ["Frozen", "Bakery"]  # Change as needed to match your DB

    for dept in departments:
        params = {
            "categories": [dept],
            "limit": 5
        }
        response = requests.get(url, params=params)
        json_resp = response.json()
        assert_db_success(json_resp, f"fetch products for department: {dept}")
        data = json_resp["data"][0]
        products = data.get("products", [])
        assert products, f"No products found for department: {dept}"
        enriched_product = None
        for p in products:
            if p.get("description") or p.get("price") or p.get("image_url"):
                enriched_product = p
                break

        assert enriched_product, f"No enriched data found for products in department: {dept}"

        print(f"\nDepartment '{dept}': found enriched product")
        print("   Product ID:", enriched_product.get("product_id"))
        print("   Name:", enriched_product.get("product_name"))
        print("   Description:", (enriched_product.get("description") or "")[:60])
        print("   Price:", enriched_product.get("price"))
        print("   Image URL:", enriched_product.get("image_url"))

class UserApiTests:
    BASE = "http://localhost:7000/users"

    def __init__(self):
        self.timestamp = int(time.time())
        self.email = f"alice_{self.timestamp}@example.com"
        self.password = f"Password123_{self.timestamp}"
        self.new_password = f"NewPass123_{self.timestamp}"
        self.updated_email = f"alice_updated_{self.timestamp}@example.com"
        self.user_id = None

    def assert_datetime_close(self, dt1_str, dt2_str, tolerance_seconds=2):
        dt1 = parse_datetime(dt1_str)
        dt2 = parse_datetime(dt2_str)
        assert abs((dt1 - dt2).total_seconds()) <= tolerance_seconds, f"{dt1} vs {dt2}"

    def create_user(self):
        data = {
            "first_name": "alice",
            "last_name": "wonderland",
            "email_address": self.email,
            "password": self.password,
            "phone_number": "123-456-7890",
            "street_address": "1 Main St",
            "city": "Townsville",
            "postal_code": "00001",
            "country": "Wonderland",
            "days_between_order_notifications": 5,
            "order_notifications_via_email": True
        }
        resp = requests.post(f"{self.BASE}/", json=data)
        json_resp = resp.json()
        assert_db_success(json_resp, "create user")
        user_json = json_resp["data"][0]
        self.user_id = user_json["user_id"]
        assert user_json["email_address"] == self.email
        assert user_json["first_name"] == "alice", f'first_name={user_json["first_name"]}'
        assert user_json["last_name"] == "wonderland", f'last_name={user_json["last_name"]}'
        print("User created:", user_json)

    def assert_datetime_offset(self, later, earlier, expected_delta_days):
        dt1 = parse_datetime(later)
        dt2 = parse_datetime(earlier)
        actual_delta = (dt1 - dt2).days
        assert actual_delta == expected_delta_days, (f"Expected {expected_delta_days} days,"
                                                     f"got {actual_delta} between {dt1} and {dt2}")
    # self.assert_datetime_close(json["order_notifications_next_scheduled_time"],
    #                            json["order_notifications_start_date_time"])


    def login_user(self, email=None, password=None, expect_success=True):
        data = {
            "email_address": email or self.email,
            "password": password or self.password
        }
        resp = requests.post(f"{self.BASE}/login", json=data)
        json_resp = resp.json()
        if expect_success:
            assert_db_success(json_resp, "login user")
            print("User logged in:", resp.json())
        else:
            assert not json_resp.get("success", True), f"Expected login to fail but success=true"
            print("Login failed as expected")

    def get_user(self):
        resp = requests.get(f"{self.BASE}/{self.user_id}")
        json_resp = resp.json()
        assert_db_success(json_resp, "get user")
        user_json = json_resp["data"][0]
        assert user_json["user_id"] == self.user_id
        assert user_json["city"] == "Townsville"
        print("User details:", user_json)

    def get_notification_settings(self):
        resp = requests.get(f"{self.BASE}/{self.user_id}/notification-settings")
        json_resp = resp.json()
        assert_db_success(json_resp, "get notification settings")
        assert json_resp["data"][0], f"Notification settings not returned: {json_resp}"
        notif = json_resp["data"][0]
        assert notif["days_between_order_notifications"] == 5
        assert notif["order_notifications_via_email"] is True
        print("Notification settings:", notif)

    def update_notification_settings(self):
        data = {
            "days_between_order_notifications": 3,
            "order_notifications_via_email": False
        }
        resp = requests.put(f"{self.BASE}/{self.user_id}/notification-settings", json=data)
        json_resp = resp.json()
        assert_db_success(json_resp, "update notification settings")
        assert json_resp["data"][0], f"Notification settings not returned: {json_resp}"
        notif = json_resp["data"][0]
        assert notif["days_between_order_notifications"] == 3
        assert notif["order_notifications_via_email"] is False
        print("Notification settings updated:", notif)

    def update_user(self):
        data = {"city": "Newville", "phone_number": "555-4321"}
        resp = requests.put(f"{self.BASE}/{self.user_id}", json=data)
        json_resp  = resp.json()
        assert_db_success(json_resp, "update user")
        user_json = json_resp["data"][0]
        assert user_json["city"] == "Newville"
        assert user_json["phone_number"] == "555-4321"
        print("User updated:", user_json)

    def update_password(self):
        data = {"current_password": self.password, "new_password": self.new_password}
        resp = requests.put(f"{self.BASE}/{self.user_id}/password", json=data)
        json_resp = resp.json()
        assert_db_success(json_resp, "update password")
        print("Password updated.")
        self.password = self.new_password

    def update_email(self):
        data = {
            "current_password": self.password,
            "new_email_address": self.updated_email
        }
        resp = requests.put(f"{self.BASE}/{self.user_id}/email", json=data)
        json_resp = resp.json()
        assert_db_success(json_resp, "update email")
        user_json = json_resp["data"][0]
        assert user_json["email_address"] == self.updated_email
        self.email = self.updated_email
        print("Email updated:", user_json)

    def delete_user(self):
        data = {"password": self.password}
        resp = requests.delete(f"{self.BASE}/{self.user_id}", json=data)
        json_resp = resp.json()
        assert_db_success(json_resp, "delete user")
        print("User deleted")

        # Check user is gone
        check = requests.get(f"{self.BASE}/{self.user_id}")
        json_resp_check = check.json()
        assert not json_resp_check.get("success", False), "Expected deleted user to not exist"
        print("Verified user is deleted")

    def run_all(self):
        self.create_user()
        self.login_user()
        self.get_user()
        self.get_notification_settings()
        self.update_notification_settings()
        self.update_user()
        self.update_password()
        self.login_user(password="wrong-password", expect_success=False)
        self.login_user()
        self.update_email()
        self.login_user()
        self.delete_user()


# TODO: add sample test for cart api


class OrderTablesSanityTest:
    def __init__(self, conn, base_url):
        self.conn = conn
        self.base_url = base_url

    def test_orders_table_basic(self):
        print("\n=== Sanity: Orders Table ===")
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders.orders")
            count = cur.fetchone()[0]
            print(f"Total orders: {count}")
            cur.execute("SELECT * FROM orders.orders LIMIT 3")
            sample = cur.fetchall()
            print("Sample orders (limit 3):")
            for row in sample:
                print(row)

    def test_order_items_table_basic(self):
        print("\n=== Sanity: Order Items Table ===")
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders.order_items")
            count = cur.fetchone()[0]
            print(f"Total order items: {count}")
            cur.execute("SELECT * FROM orders.order_items LIMIT 3")
            sample = cur.fetchall()
            print("Sample order items (limit 3):")
            for row in sample:
                print(row)

    def test_order_items_relationship(self):
        print("\n=== Sanity: Order → Order Items Relationship ===")
        with self.conn.cursor() as cur:
            cur.execute("SELECT order_id FROM orders.orders OFFSET floor(random()*10000) LIMIT 1")
            row = cur.fetchone()
            if not row:
                print("No orders found.")
                return
            order_id = row[0]
            # order_id = 2468802
            print(f"Random order_id: {order_id}")
            cur.execute("SELECT * FROM orders.order_items WHERE order_id = %s LIMIT 3", (order_id,))
            items = cur.fetchall()
            if items:
                print(f"Sample order_items for order_id={order_id}:")
                for item in items:
                    print(item)
            else:
                print(f"No order_items found for order_id={order_id}.")

    def test_orders_api(self):
        import requests
        print("\n=== Sanity: GET /orders API ===")
        url = f"{self.base_url}/orders?limit=2"
        try:
            r = requests.get(url)
            print(f"GET {url} - Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print("Response:", data)
            else:
                print("Error response:", r.text)
        except Exception as e:
            print("API call failed:", e)

    def test_order_items_api(self):
        import requests
        print("\n=== Sanity: GET /orders/{id}/items API ===")
        url = f"{self.base_url}/orders?limit=2"
        try:
            r = requests.get(url)
            if r.status_code != 200:
                print("Cannot fetch orders for item test.")
                return
            orders = r.json().get("orders") or r.json()
            if not orders:
                print("No orders returned from API.")
                return
            for order in orders:
                order_id = order.get("order_id") or order.get("id")
                item_url = f"{self.base_url}/orders/{order_id}/items"
                r2 = requests.get(item_url)
                print(f"GET {item_url} - Status: {r2.status_code}")
                if r2.status_code == 200:
                    print("Items:", r2.json())
                else:
                    print("Error response:", r2.text)
        except Exception as e:
            print("API call failed:", e)



if __name__ == "__main__":
    test_query()
    print()
    # test_get_products()
    # print()
    # test_create_order()
    # print()
    # test_orders_order_id_items()
    # print()
    # test_delete_order()
    print()
    tester = UserApiTests()
    tester.run_all()
    print()
    # test_enriched_products_across_departments()
    print()

    # #### testing orders and order_items in db
    # conn = psycopg2.connect(
    #     host="localhost",
    #     port=5432,
    #     user="timele_user",
    #     password="timele_password",
    #     database="timele_db"
    # )
    # base_url = "http://localhost:7000"
    # sanity = OrderTablesSanityTest(conn, base_url)
    # sanity.test_orders_table_basic()
    # sanity.test_order_items_table_basic()
    # sanity.test_order_items_relationship()
    # sanity.test_orders_api()
    # sanity.test_order_items_api()
    # conn.close()
