import pandas as pd
from datetime import timedelta, time, datetime, UTC
import random

def random_evening_time():
    # 60% evening (17:00-23:00)
    if random.random() < 0.6:
        hour = random.randint(17, 23)
    else:
        hour = random.choice(list(range(5, 24)) + [0, 1])
    minute = random.randint(0, 59)
    return time(hour=hour, minute=minute)

def assign_datetime(base_date):
    t = random_evening_time()
    return datetime.combine(base_date.date(), t, tzinfo=UTC)

status_paths = [
    (['pending', 'processing', 'shipped', 'delivered'], 0.75),
    (['pending', 'processing', 'cancelled'], 0.10),
    (['pending', 'processing', 'failed'], 0.03),
    (['pending', 'processing', 'shipped', 'delivered', 'return_requested', 'returned', 'refunded'], 0.07),
    (['pending', 'processing', 'shipped', 'delivered', 'refunded'], 0.05),
]

def choose_status_path():
    r = random.random()
    acc = 0
    for path, prob in status_paths:
        acc += prob
        if r < acc:
            return path
    return status_paths[0][0]  # Fallback

def generate_status_timestamps(base_datetime, path):
    ts = [base_datetime]
    for i in range(1, len(path)):
        prev = ts[-1]
        if path[i] == 'processing':
            next_base = prev + timedelta(minutes=random.randint(5, 60))
        elif path[i] == 'shipped':
            next_base = prev + timedelta(hours=random.randint(1, 36))
        elif path[i] == 'delivered':
            next_base = prev + timedelta(days=random.randint(1, 7))
        elif path[i] in ['cancelled', 'failed']:
            next_base = prev + timedelta(minutes=random.randint(10, 120))
        elif path[i] == 'return_requested':
            next_base = prev + timedelta(days=random.randint(1, 15))
        elif path[i] == 'returned':
            next_base = prev + timedelta(days=random.randint(1, 7))
        elif path[i] == 'refunded':
            next_base = prev + timedelta(days=random.randint(0, 5))
        else:
            next_base = prev + timedelta(hours=1)
        # Assign a new plausible time for each status (can cross to next day, simulating event randomness)
        next_dt = assign_datetime(next_base)
        # Ensure status times are monotonic (never before previous status)
        if next_dt <= prev:
            next_dt = prev + timedelta(minutes=random.randint(1, 90))
        ts.append(next_dt)
    return ts

def generate_orders_demo_status_history():
    print("Reading input CSV...")
    orders = pd.read_csv('orders_demo_enriched.csv')
    print(f"Loaded {len(orders)} orders.")

    orders['created_at'] = pd.to_datetime(orders['created_at'], utc=True)
    output = []

    for _, row in orders.iterrows():
        order_id = row['order_id']
        base_dt = row['created_at']
        path = choose_status_path()
        timestamps = generate_status_timestamps(base_dt, path)
        for status, status_time in zip(path, timestamps):
            output.append({
                'order_id': order_id,
                'status': status,
                'changed_at': status_time.isoformat(sep=' ')  # Includes +00:00
            })

    order_status_history = pd.DataFrame(output)
    order_status_history.to_csv('orders_demo_status_history.csv', index=False)
    print("orders_demo_status_history.csv created.")

if __name__ == "__main__":
    generate_orders_demo_status_history()

