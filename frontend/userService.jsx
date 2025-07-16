const API_BASE_URL = "http://localhost:8000/api";

export async function createUser(userData) {
  const response = await fetch(`${API_BASE_URL}/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(userData)
  });

  if (!response.ok) {
    throw new Error("Failed to create user");
  }

  return await response.json();
}

// FastAPI request
export async function  sendAddItemToCartRequest(user_id, item) {
  const payload = {
    item_id: item.id,
    user_id: user_id,
    quantity: item.quantity
  };

  const response = await fetch(`${API_BASE_URL}/cart/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Failed to add item to cart");
  }

  return await response.json();
}
