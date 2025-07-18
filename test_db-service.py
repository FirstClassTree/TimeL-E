import requests
import json
# from uuid_utils import uuid7

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

        # Raise error if response code is not 200
        response.raise_for_status()

        # Print the response in a pretty way
        print("Status:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))

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
    print("Status code:", response.status_code)
    print("Response JSON:")
    print(response.json())

def test_create_order():
    url = "http://localhost:7000/orders"
    payload = {
        "user_id": "01981762-2cc0-740e-a010-df99a9bbc9d5",  # replace with a real user_id from DB
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
        print("Status code:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
        # assert response.status_code == 201
    except requests.RequestException as e:
        print("HTTP request failed:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Server response:", e.response.text)
    except Exception as e:
        print("General error:", e)
        test_create_order()


def test_orders_order_id_items():
    order_id = "01981768-0d9d-723b-ac39-fd8fbdc2eadb"
    items = [
        {"product_id": 1, "quantity": 2},
        {"product_id": 5, "quantity": 1},
    ]

    resp = requests.post(
        f"http://localhost:7000/orders/{order_id}/items",
        json=items  # Items as list, not wrapped in a dict
    )
    print(resp.status_code)
    print(resp.json())

class UserApiTests:
    BASE = "http://localhost:7000/users"

    def __init__(self):
        self.user_id = None
        self.password = "Password123"
        self.new_password = "NewPass123"

    def create_user(self):
        data = {
            "name": "alice",
            "email_address": "alice@example.com",
            "password": self.password,
            "phone_number": "123-456-7890",
            "street_address": "1 Main St",
            "city": "Townsville",
            "postal_code": "00001",
            "country": "Wonderland"
        }
        resp = requests.post(f"{self.BASE}/", json=data)
        assert resp.status_code == 201, resp.text
        self.user_id = resp.json()["user_id"]
        print("User created:", resp.json())

    def get_user(self):
        resp = requests.get(f"{self.BASE}/{self.user_id}")
        assert resp.status_code == 200, resp.text
        print("User details:", resp.json())

    def update_user(self):
        data = {"city": "Newville", "phone_number": "555-4321"}
        resp = requests.patch(f"{self.BASE}/{self.user_id}", json=data)
        assert resp.status_code == 200, resp.text
        print("User updated:", resp.json())

    def update_password(self):
        data = {"current_password": self.password, "new_password": self.new_password}
        resp = requests.post(f"{self.BASE}/{self.user_id}/password", json=data)
        assert resp.status_code == 200, resp.text
        print("Password updated:", resp.json())
        self.password = self.new_password  # Update for later deletion

    def delete_user(self):
        data = {"password": self.password}
        resp = requests.delete(f"{self.BASE}/{self.user_id}", json=data)
        assert resp.status_code in (200, 204), resp.text
        print("User deleted.")

    def run_all(self):
        self.create_user()
        self.get_user()
        self.update_user()
        self.update_password()
        self.delete_user()


if __name__ == "__main__":
    test_query()
    print()
    test_get_products()
    print()
    test_create_order()
    print()
    test_orders_order_id_items()
    print()
    tester = UserApiTests()
    tester.run_all()

