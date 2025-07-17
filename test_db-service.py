import requests
import json

# Endpoint URL
url = "http://localhost:7000/query"

# The payload: use $1, $2 as parameter placeholders
payload = {
    "sql": "SELECT * FROM products.products WHERE department_id = $1 LIMIT $2",
    "params": [19, 10]
}

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
