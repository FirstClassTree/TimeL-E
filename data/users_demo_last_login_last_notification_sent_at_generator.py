import pandas as pd
from datetime import datetime, timedelta, UTC
import random

# --- Settings ---
USERS_CSV = "users_demo.csv"
ORDERS_CSV = "orders_demo_enriched.csv"
STATUS_CSV = "orders_demo_status_history.csv"
FALLBACK_START = datetime(2016, 1, 1, tzinfo=UTC)
FALLBACK_END = datetime(2017, 1, 1, tzinfo=UTC)
fallback_range = int((FALLBACK_END - FALLBACK_START).total_seconds())

# Helper: get a random timedelta in range
def random_timedelta(days=0, hours=0, minutes=0, seconds=0):
    total_seconds = (
            days * 86400 +
            hours * 3600 +
            minutes * 60 +
            seconds
    )
    if total_seconds == 0:
        return timedelta(0)
    return timedelta(seconds=random.randint(1, total_seconds))

def generate_users_demo_last_login_and_notification():
    # --- 1. Load CSVs ---
    df_users = pd.read_csv(USERS_CSV)
    df_orders = pd.read_csv(ORDERS_CSV)
    df_status = pd.read_csv(STATUS_CSV)

    # Convert date columns to timezone-aware datetime
    df_orders['created_at'] = pd.to_datetime(df_orders['created_at'], utc=True)
    df_status['changed_at'] = pd.to_datetime(df_status['changed_at'], utc=True)

    last_login_list = []
    last_notif_list = []

    for idx, row in df_users.iterrows():
        user_id = row['user_id']
        first_name = str(row.get('first_name', '')).strip()
        is_demo = first_name.lower().startswith("demo")

        # a. Find all user's orders, pick latest by created_at
        user_orders = df_orders[df_orders['user_id'] == user_id]
        if not user_orders.empty:
            latest_order = user_orders.loc[user_orders['created_at'].idxmax()]
            latest_order_id = latest_order['order_id']
            latest_created_at = latest_order['created_at']
        else:
            # Fallback: No orders, use a random date between 1.1.16-1.1.17
            random_seconds = random.randint(0, fallback_range)
            base_time = FALLBACK_START + timedelta(seconds=random_seconds)
            last_login_list.append(base_time)
            last_notif_list.append(base_time)
            continue

        if not is_demo:
            # Normal users: random 0-7 days after latest order
            delta = random_timedelta(days=7)
            t = latest_created_at + delta
            last_notif_list.append(t)
            # Login a few seconds to 10 minutes after notification
            t2 = t + random_timedelta(minutes=10)
            last_login_list.append(t2)
        else:
            # DEMO users
            # Get all status changes for their latest order
            status_changes = df_status[df_status['order_id'] == latest_order_id].sort_values('changed_at')
            if not status_changes.empty:
                # Pick one status change (random or first) after latest_created_at
                after_order = status_changes[status_changes['changed_at'] > latest_created_at]
                if after_order.empty:
                    # Fallback: before any status changes
                    first_status = status_changes.iloc[0]
                    target_time = first_status['changed_at'] - timedelta(minutes=random.randint(5, 120))
                else:
                    chosen_status = after_order.iloc[random.randint(0, len(after_order) - 1)]
                    # Notification sent shortly before that change
                    target_time = chosen_status['changed_at'] - timedelta(minutes=random.randint(2, 30))
                last_notif_list.append(target_time)
                last_login_list.append(target_time + timedelta(seconds=random.randint(10, 300)))
            else:
                # Fallback if no status history, act like normal user
                delta = random_timedelta(days=2)
                t = latest_created_at + delta
                last_notif_list.append(t)
                last_login_list.append(t + random_timedelta(minutes=10))

    # --- 4. Update users DataFrame ---
    df_users['last_login'] = [d.isoformat(sep=' ') for d in last_login_list]
    df_users['last_notifications_viewed_at'] = [d.isoformat(sep=' ') for d in last_notif_list]

    # --- 5. Overwrite users_demo.csv ---
    df_users.to_csv(USERS_CSV, index=False)

    print(f"Updated {USERS_CSV} with last_login and last_notifications_viewed_at columns.")

if __name__ == "__main__":
    generate_users_demo_last_login_and_notification()

