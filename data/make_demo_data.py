# Demo Data Extraction Script - Run in /data/ with source CSVs present
# run on host

import pandas as pd
import numpy as np
from faker import Faker
import random
import bcrypt

# Configs
ORDERS_CSV = 'orders.csv'
ORDER_PRIOR_CSV = 'order_products__prior.csv'
# ORDER_TRAIN_CSV = 'order_products__train.csv'
ORDERS_DEMO_CSV = 'orders_demo.csv'
ORDER_ITEMS_DEMO_CSV = 'order_items_demo.csv'
USERS_DEMO_CSV = 'users_demo.csv'
NUM_USERS = 1000
SEED = 42

random.seed(SEED)
np.random.seed(SEED)

# Step 1: Select 1,000 test users
orders = pd.read_csv(ORDERS_CSV)
test_users = orders[orders['eval_set'] == 'test']['user_id'].unique()
selected_users = np.random.choice(test_users, NUM_USERS, replace=False)

# Step 2: Pull all orders for those users
orders_demo = orders[orders['user_id'].isin(selected_users)]
orders_demo.to_csv(ORDERS_DEMO_CSV, index=False)

# Step 3: Pull all order_items for those orders
order_ids = orders_demo['order_id'].unique()
order_items = []

for fname in [ORDER_PRIOR_CSV]:
    chunk_iter = pd.read_csv(fname, chunksize=100_000)
    for chunk in chunk_iter:
        filtered = chunk[chunk['order_id'].isin(order_ids)]
        order_items.append(filtered)

order_items_demo = pd.concat(order_items, ignore_index=True)
order_items_demo.to_csv(ORDER_ITEMS_DEMO_CSV, index=False)

# Step 4: Generate fake user info
fake = Faker()
users_info = []

for user_id in selected_users:
    name = fake.name()
    # Generate a deterministic password hash for the demo
    password = 'password123'
    # Use bcrypt instead of sha256
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    email_address = fake.email()
    phone_number = fake.phone_number()
    street_address = fake.street_address()
    city = fake.city()
    postal_code = fake.postcode()
    country = fake.country()
    users_info.append([
        user_id, name, hashed_password, email_address, phone_number,
        street_address, city, postal_code, country
    ])

users_demo_df = pd.DataFrame(
    users_info,
    columns=[
        "user_id", "name", "hashed_password", "email_address", "phone_number",
        "street_address", "city", "postal_code", "country"
    ]
)
users_demo_df.to_csv(USERS_DEMO_CSV, index=False)

print("  Demo CSVs generated:")
print(f"  Users: {USERS_DEMO_CSV} ({len(users_demo_df)})")
print(f"  Orders: {ORDERS_DEMO_CSV} ({len(orders_demo)})")
print(f"  Order Items: {ORDER_ITEMS_DEMO_CSV} ({len(order_items_demo)})")

