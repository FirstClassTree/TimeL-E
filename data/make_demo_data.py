# Demo Data Extraction Script - Run in /data/ with source CSVs present
# run on host

import pandas as pd
import numpy as np
from faker import Faker
import random
from argon2 import PasswordHasher
import secrets
import string

from orders_demo_enricher import generate_orders_demo_enriched
from orders_demo_status_history_generator import generate_orders_demo_status_history
from users_demo_last_login_last_notification_sent_at_generator import generate_users_demo_last_login_and_notification


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

# Argon2id password hasher config
ph = PasswordHasher(
    memory_cost=65536,  # 64 MB
    time_cost=3,        # 3 iterations
    parallelism=4,      # 4 threads
    hash_len=32,        # 32 byte hash
    salt_len=16         # 16 byte salt
)


def random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password: str) -> str:
    return ph.hash(password)

def main():
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

    # Step 4: Generate fake user info with first and last names
    fake = Faker()
    users_info = []
    used_emails = set()

    for user_id in selected_users:
        first_name = fake.first_name()
        last_name = fake.last_name()
        # generate random password and hash with Argon2id
        password = random_password()
        hashed_password = hash_password(password)
        # Ensure email uniqueness
        while True:
            email_address = fake.email()
            if email_address not in used_emails:
                used_emails.add(email_address)
                break
        phone_number = fake.phone_number()
        street_address = fake.street_address()
        city = fake.city()
        postal_code = fake.postcode()
        country = fake.country()
        users_info.append([
            user_id, first_name, last_name, password, hashed_password, email_address, phone_number,
            street_address, city, postal_code, country
        ])

    users_demo_df = pd.DataFrame(
        users_info,
        columns=[
            "user_id", "first_name", "last_name", "password", "hashed_password", "email_address", "phone_number",
            "street_address", "city", "postal_code", "country"
        ]
    )
    users_demo_df.to_csv(USERS_DEMO_CSV, index=False)

    print("  Demo CSVs generated:")
    print(f"  Users: {USERS_DEMO_CSV} ({len(users_demo_df)})")
    print(f"  Orders: {ORDERS_DEMO_CSV} ({len(orders_demo)})")
    print(f"  Order Items: {ORDER_ITEMS_DEMO_CSV} ({len(order_items_demo)})")

    # ---- Step 5: Generate timestamps for order.created_at, orderstatushistory.changed_at, users.last_login, users.last_notification_sent_at ----

    print("Generating orders_demo_created_at.csv ...")
    generate_orders_demo_enriched()

    print("Generating orders_demo_status_history.csv ...")
    generate_orders_demo_status_history()

    print("Adding last_login and last_notification_sent_at to users_demo.csv ...")
    generate_users_demo_last_login_and_notification()
    print("All demo data files are now ready!")

    print("All demo data including timestamps generated and ready.")

if __name__ == "__main__":
    main()

