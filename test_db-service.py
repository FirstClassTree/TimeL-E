import requests
import json

def test_query():
    # Endpoint URL
    url = "http://localhost:7000/query"

    # The payload: use $1, $2 as parameter placeholders
    payload = {
        "sql": "SELECT * FROM products.products WHERE department_id = $1 LIMIT $2",
        "params": [19, 10]
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
        "user_id": 1,  # replace with a real user_id from DB
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
        assert response.status_code == 201
    except requests.RequestException as e:
        print("HTTP request failed:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Server response:", e.response.text)
    except Exception as e:
        print("General error:", e)
        test_create_order()


if __name__ == "__main__":
    test_query()
    test_get_products()
