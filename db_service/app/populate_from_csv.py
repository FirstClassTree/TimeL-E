import os
import csv
import traceback

from sqlalchemy import func, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta, UTC
from sqlalchemy import Uuid
import uuid
import pandas as pd
from .db_core.database import SessionLocal
from .db_core.models import Product, Department, Aisle, User, Order, OrderItem
from .db_core.config import settings

CSV_DIR = "/data"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # match CSV, ISO 8601 format

def parse_dt(dt_str):
    if not dt_str or pd.isna(dt_str):
        return None
    # Try ISO8601 first (for new CSVs), else fallback
    try:
        dt = pd.to_datetime(dt_str, utc=True)
        return dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt
    except Exception:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=UTC)

def load_departments(db: Session):
    departments_file = os.path.join(CSV_DIR, "departments.csv")
    print(f"Loading departments from: {departments_file}")
    with open(departments_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Department(
                department_id=int(row["department_id"]),
                department=row["department"]
            ))
    db.commit()

def load_aisles(db: Session):
    aisles_file = os.path.join(CSV_DIR, "aisles.csv")
    print(f"Loading aisles from: {aisles_file}")
    with open(aisles_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Aisle(
                aisle_id=int(row["aisle_id"]),
                aisle=row["aisle"]
            ))
    db.commit()

def load_products(db: Session):
    products_file = os.path.join(CSV_DIR, "products.csv")
    print(f"Loading products from: {products_file}")
    batch_size = 200  # Reduced for memory stability
    batch_products = []
    products_loaded = 0
    product_errors = 0
    success_count = 0
    with open(products_file, newline='') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            try:
                product = Product(
                    product_id=int(row["product_id"]),
                    product_name=row["product_name"],
                    aisle_id=int(row["aisle_id"]),
                    department_id=int(row["department_id"])
                )
                batch_products.append(product)
                products_loaded += 1

                if len(batch_products) >= batch_size:
                    try:
                        db.add_all(batch_products)
                        db.flush()  # Optionally use commit for ultra-safety
                        success_count += len(batch_products)
                        if success_count % 10000 == 0:
                            print(f"   Committed batch of {len(batch_products)} products")
                        batch_products = []
                    except (IntegrityError, SQLAlchemyError) as batch_err:
                        db.rollback()
                        print(f"   ERROR[load products]: Batch insert failed at row {row_num} (will try individually): {batch_err}")
                        # Now try each row one by one to isolate the bad ones
                        for single_product in batch_products:
                            try:
                                db.add(single_product)
                                db.flush()
                                success_count += 1
                            except (IntegrityError, SQLAlchemyError) as row_err:
                                product_errors += 1
                                db.rollback()
                                print(f"      -> Skipping bad product (row {row_num}): {row_err}")
                        batch_products = []

            except Exception as row_error:
                product_errors += 1
                print(f"   Row {row_num}: Error creating product: {row_error}")
                print(f"Row data: {row}")

        # Commit any remaining products in the final batch
        if batch_products:
            try:
                db.add_all(batch_products)
                db.flush()
                print(f"   Committed final batch of {len(batch_products)} products")
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR[load products]: Final batch insert failed (will try individually): {batch_err}")
                success_count_final = 0
                for single_product in batch_products:
                    try:
                        db.add(single_product)
                        db.flush()
                        success_count_final += 1
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        product_errors += 1
                        db.rollback()
                        print(f"      -> Skipping bad product: {row_err}")
                print(f"   Committed final batch of {success_count_final} products")

        print(f"Products processing summary:")
        print(f"   Successfully prepared: {products_loaded} products")
        print(f"   Skipped/Errors: {product_errors}")

        db.commit()

def load_orders(db: Session):
    orders_file = os.path.join(CSV_DIR, "orders_demo_enriched.csv")
    users_file = os.path.join(CSV_DIR, "users_demo.csv")
    print(f"Loading orders from: {orders_file}")

    # Set sequence starting point for new orders (3422000+)
    # Orders now use simple integer IDs starting from CSV data range
    from sqlalchemy import text
    db.execute(text("SELECT setval('orders.orders_id_seq', 3422000, false)"))
    print("Set orders.id sequence to start at 3422000 for new orders (single integer ID architecture)")

    # Pre-load all existing user internal IDs for foreign key validation
    print("Pre-loading existing user internal IDs for foreign key validation...")
    existing_users = set()
    users = db.query(User.id).all()
    for user in users:
        existing_users.add(user.id)
    print(f"Found {len(existing_users)} existing users for validation")
    
    if len(existing_users) == 0:
        print("   WARNING: No users found in database!")
        print("   Make sure users are loaded before orders")
        print("   Continuing anyway - will skip all orders with FK violations")

    # Preload user address info by user_id for fast lookup
    user_info = {}
    if os.path.exists(users_file):
        with open(users_file, newline='', encoding='utf-8') as uf:
            reader = csv.DictReader(uf)
            for row in reader:
                first_name = row.get('first_name') or ''
                last_name = row.get('last_name') or ''
                user_info[int(row['user_id'])] = {
                    'delivery_name': f"{first_name} {last_name}".strip(),
                    'phone_number': row.get('phone_number'),
                    'street_address': row.get('street_address'),
                    'city': row.get('city'),
                    'postal_code': row.get('postal_code'),
                    'country': row.get('country'),
                }

    batch_size = 200  # Reduced to prevent segfaults
    batch_orders = []
    orders_loaded = 0
    order_errors = 0
    fk_violations = 0
    success_count = 0

    with open(orders_file, newline='') as f:
        reader = csv.DictReader(f)
        # Detect field presence once
        has_created_at = 'created_at' in (reader.fieldnames or [])
        has_tracking_number = 'tracking_number' in (reader.fieldnames or [])
        has_shipping_carrier = 'shipping_carrier' in (reader.fieldnames or [])
        has_tracking_url = 'tracking_url' in (reader.fieldnames or [])

        for row_num, row in enumerate(reader, 1):
            try:
                integer_user_id = int(row['user_id'])

                # VALIDATE FOREIGN KEY BEFORE CREATING OBJECT
                # Check against internal user IDs
                if integer_user_id not in existing_users:
                    fk_violations += 1
                    if fk_violations <= 10:  # Show first 10 violations
                        print(f"   Row {row_num}: Skipping order with invalid user_id {integer_user_id}")
                    elif fk_violations == 11:
                        print(f"   ... (suppressing further FK violation messages)")
                    continue

                # Get address/phone from preloaded dict
                uinfo = user_info.get(integer_user_id, {})
                order = Order(
                    id=int(row["order_id"]),  # Use original CSV order ID as single integer ID
                    user_id=integer_user_id,  # Use internal user ID for FK relationship
                    order_number=int(row["order_number"]),
                    order_dow=int(row["order_dow"]),
                    order_hour_of_day=int(row["order_hour_of_day"]),
                    days_since_prior_order=int(float(row["days_since_prior_order"])) if row.get(
                        "days_since_prior_order") else None,
                    total_items=0,  # count them when finished loading
                    created_at=parse_dt(row.get('created_at')) if has_created_at else None,
                    tracking_number=row['tracking_number'] if has_tracking_number else None,
                    shipping_carrier=row['shipping_carrier'] if has_shipping_carrier else None,
                    tracking_url=row['tracking_url'] if has_tracking_url else None,
                    delivery_name=uinfo.get('delivery_name'),
                    phone_number=uinfo.get('phone_number'),
                    street_address=uinfo.get('street_address'),
                    city=uinfo.get('city'),
                    postal_code=uinfo.get('postal_code'),
                    country=uinfo.get('country'),
                )
                batch_orders.append(order)
                orders_loaded += 1

                if len(batch_orders) >= batch_size:
                    try:
                        db.add_all(batch_orders)
                        db.flush()  # Optionally use commit for ultra-safety
                        success_count += len(batch_orders)
                        if success_count % 10000 == 0:
                            print(f"   Committed batch of {len(batch_orders)} orders")
                        batch_orders = []
                    except (IntegrityError, SQLAlchemyError) as batch_err:
                        db.rollback()
                        print(f"   ERROR[load orders]: Batch insert failed at row {row_num} (will try individually): {batch_err}")
                        # Now try each row one by one to isolate the bad ones
                        for single_order in batch_orders:
                            try:
                                db.add(single_order)
                                db.flush()
                                success_count += 1
                            except (IntegrityError, SQLAlchemyError) as row_err:
                                order_errors += 1
                                db.rollback()
                                print(f"      -> Skipping bad order (row {row_num}): {row_err}")
                        batch_orders = []

            except Exception as row_error:
                order_errors += 1
                print(f"   Row {row_num}: Error creating order: {row_error}")

        # Commit any remaining orders in the final batch
        if batch_orders:
            try:
                db.add_all(batch_orders)
                db.flush()
                success_count += len(batch_orders)
                print(f"   Committed final batch of {len(batch_orders)} orders")
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR[load orders]: Final batch insert failed (will try individually): {batch_err}")
                success_count_final = 0
                for single_order in batch_orders:
                    try:
                        db.add(single_order)
                        db.flush()
                        success_count_final += 1
                        success_count += 1
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        order_errors += 1
                        db.rollback()
                        print(f"      -> Skipping bad order: {row_err}")
                print(f"   Committed final batch of {success_count_final} orders")

        print(f"Orders processing summary:")
        print(f"   Successfully loaded: {orders_loaded} orders")
        if fk_violations > 0:
            print(f"   Skipped FK violations: {fk_violations} orders")
        if order_errors > 0:
            print(f"   Other errors: {order_errors} orders")
        print(f"   Total committed: {success_count}")

        db.commit()

def load_order_items(db: Session):
    order_items_file = os.path.join(CSV_DIR, "order_items_demo.csv")
    print(f"Loading order items from: {order_items_file}")
    
    # Pre-load all existing order_ids for validation
    print("Pre-loading existing order_ids for foreign key validation...")
    existing_orders = set()
    orders = db.query(Order.id).all()
    for order in orders:
        existing_orders.add(order.id)
    print(f"Found {len(existing_orders)} existing orders for validation")
    
    batch_size = 200  # Reduced to prevent segfaults
    batch_items = []
    items_loaded = 0
    item_errors = 0
    fk_violations = 0
    success_count = 0
    
    with open(order_items_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            try:
                order_id = int(row["order_id"])
                
                # VALIDATE FOREIGN KEY BEFORE CREATING OBJECT
                if order_id not in existing_orders:
                    fk_violations += 1
                    if fk_violations <= 10:  # Show first 10 violations
                        print(f"   Row {row_num}: Skipping order_item with invalid order_id {order_id}")
                    elif fk_violations == 11:
                        print(f"   ... (suppressing further FK violation messages)")
                    continue
                
                item = OrderItem(
                    order_id=order_id,
                    product_id=int(row["product_id"]),
                    add_to_cart_order=int(row.get("add_to_cart_order") or 1),
                    reordered=int(row.get("reordered") or 0),
                )
                batch_items.append(item)
                items_loaded += 1

                if len(batch_items) >= batch_size:
                    try:
                        db.add_all(batch_items)
                        db.flush()  # Use flush instead of commit for consistency
                        success_count += len(batch_items)
                        if success_count % 10000 == 0:
                            print(f"   Committed batch of {len(batch_items)} order items ({success_count} total)")
                        batch_items = []
                    except (IntegrityError, SQLAlchemyError) as batch_err:
                        db.rollback()
                        print(f"   ERROR[load order items]: Batch insert failed at row {row_num} (will try individually): {batch_err}")
                        # Now try each row one by one to isolate the bad ones
                        for single_item in batch_items:
                            try:
                                db.add(single_item)
                                db.flush()
                                success_count += 1
                            except (IntegrityError, SQLAlchemyError) as row_err:
                                item_errors += 1
                                db.rollback()
                                print(f"      -> Skipping bad order item (row {row_num}): {row_err}")
                        batch_items = []
            except Exception as row_error:
                item_errors += 1
                print(f"   Row {row_num}: Error creating order item: {row_error}")
        
        if batch_items:
            try:
                db.add_all(batch_items)
                db.flush()
                success_count += len(batch_items)
                print(f"   Committed final batch of {len(batch_items)} order items")
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR[load order items]: Final batch insert failed (will try individually): {batch_err}")
                success_count_final = 0
                for single_order_item in batch_items:
                    try:
                        db.add(single_order_item)
                        db.flush()
                        success_count_final += 1
                        success_count += 1
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        item_errors += 1
                        db.rollback()
                        print(f"      -> Skipping bad order item: {row_err}")
                print(f"   Committed final batch of {success_count_final} order items")

    print(f"Order Items processing summary:")
    print(f"   Successfully loaded: {items_loaded} order items")
    print(f"   Skipped FK violations: {fk_violations}")
    print(f"   Other errors: {item_errors}")
    print(f"   Total committed: {success_count}")

    db.commit()

def _dev_overwrite_user_from_csv(existing_user, csv_row, db, row_num):
    """
    Helper: Overwrites an existing user object with values from csv_row.
    Prints full dicts of old and new user details for transparency.
    Dynamically updates all fields present in the CSV (except 'user_id').
    """
    old_dict = dict(existing_user.__dict__)
    old_dict.pop('_sa_instance_state', None)
    print(
        f"Row {row_num}: DEV MODE: User with ID {csv_row['user_id']} already exists "
        f"and is being OVERWRITTEN by Demo user from CSV.\n"
        f"Old user details: {old_dict}\n"
        f"New (Demo) user details: {csv_row}"
    )

    # Datetime fields to parse
    dt_fields = ['last_login', 'last_notifications_viewed_at', 'order_notifications_start_date_time',
    'last_notification_sent_at', 'order_notifications_next_scheduled_time']

    skip_fields = ["user_id", "external_user_id"]

    for field, val in csv_row.items():
        if field in skip_fields:  # Don't update the primary key or external user id
            continue
        if field in dt_fields and val and val.strip():
            try:
                val = parse_dt(val)
            except Exception as e:
                print(f"Warning: Could not parse datetime for {field}: {val} ({e})")
                val = None
        setattr(existing_user, field, val)

    # default logic for derived fields
    if csv_row.get("last_login"):
        last_login_dt = parse_dt(csv_row["last_login"])
        existing_user.order_notifications_start_date_time = last_login_dt
        existing_user.order_notifications_next_scheduled_time = last_login_dt + timedelta(days=7) if last_login_dt else None
        existing_user.last_notification_sent_at = last_login_dt

    existing_user.days_between_order_notifications = 7
    existing_user.pending_order_notification = True

    db.flush()

def load_users(db: Session):
    USER_UUID_NAMESPACE = uuid.UUID('cafebabe-1234-4abc-8def-c0ffeefeed01')  # change for prod

    # a common migration approach if for deterministic external IDs from legacy integer PKs;
    def deterministic_uuid_from_int(integer_id: int) -> uuid.UUID:
        return uuid.uuid5(USER_UUID_NAMESPACE, str(integer_id))  # uuid5 for stable, unique, deterministic UUIDs

    users_file = os.path.join(CSV_DIR, "users_demo.csv")
    print(f"Loading users from: {users_file}")

    if not os.path.exists(users_file):
        print(f"ERROR: Users file not found: {users_file}")
        print("Available files in directory:")
        for f in os.listdir(CSV_DIR):
            print(f"   - {f}")
    else:
        print(f"Users file exists: {users_file}")
        file_size = os.path.getsize(users_file)
        print(f"File size: {file_size} bytes")

        # Set sequence starting point for new users (400000+)
        from sqlalchemy import text
        db.execute(text("SELECT setval('users.users_id_seq', 400000, false)"))
        print("Set users.id sequence to start at 400000 for new users")

        users_loaded = 0
        errors = 0
        batch_size = 100  # Reduced for memory stability

        with open(users_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print(f"CSV columns: {reader.fieldnames}")

            batch_users = []
            for row_num, row in enumerate(reader, 1):
                try:
                    # Use original CSV user_id as internal ID (1-201520 range)
                    integer_user_id = int(row['user_id'])
                    
                    # Check for unique constraint violations before adding
                    existing_user_id = db.query(User).filter(User.id == integer_user_id).first()
                    existing_email = db.query(User).filter(User.email_address == row['email_address']).first()

                    if existing_user_id:
                        if settings.NODE_ENV == "development" and row["first_name"] == "Demo":
                            _dev_overwrite_user_from_csv(existing_user_id, row, db, row_num)
                            users_loaded += 1
                            continue
                        else:
                            if errors < 3:
                                print(f"   Row {row_num}: User ID {row['user_id']} already exists, skipping")
                            errors += 1
                            continue

                    if existing_email:
                        if errors < 3:
                            print(f"   Row {row_num}: Email '{row['email_address']}' already exists, skipping")
                        errors += 1
                        continue

                    external_user_id = deterministic_uuid_from_int(integer_user_id)     # Use original CSV ID to generate external ID

                    user = User(
                        id=integer_user_id,  # Use original CSV ID as internal ID
                        external_user_id=external_user_id,
                        first_name=row.get('first_name'),
                        last_name=row.get('last_name'),
                        hashed_password=row.get('hashed_password'),
                        email_address=row.get('email_address'),
                        phone_number=row.get('phone_number'),
                        street_address=row.get('street_address'),
                        city=row.get('city'),
                        postal_code=row.get('postal_code'),
                        country=row.get('country'),
                        last_login=parse_dt(row.get('last_login')),
                        last_notifications_viewed_at=parse_dt(row.get('last_notifications_viewed_at')),
                        days_between_order_notifications=7,
                        order_notifications_start_date_time=parse_dt(row.get('last_login')),
                        order_notifications_next_scheduled_time=(
                            lambda last_login_dt: last_login_dt + timedelta(days=7) if last_login_dt else None
                        )(parse_dt(row.get('last_login'))),
                        last_notification_sent_at=parse_dt(row.get('last_login')),
                        pending_order_notification=True
                    )
                    batch_users.append(user)
                    users_loaded += 1

                    if users_loaded <= 5:  # Show first 5 for confirmation
                        print(f"   Row {row_num}: Prepared user {row['user_id']}: {row['first_name']} {row['last_name']}")

                    # Commit in batches
                    if len(batch_users) >= batch_size:
                        try:
                            db.add_all(batch_users)
                            db.flush()  # Flush to catch constraint errors
                            print(f"   Committed batch of {len(batch_users)} users")
                        except (IntegrityError, SQLAlchemyError) as batch_err:
                            db.rollback()
                            print(
                                f"   ERROR: User batch insert failed at row {row_num} (will try individually): {batch_err}")
                            for user in batch_users:
                                try:
                                    db.add(user)
                                    db.flush()
                                except (IntegrityError, SQLAlchemyError) as row_err:
                                    errors += 1
                                    db.rollback()
                                    print(f"      -> Skipping bad user (row {row_num}): {row_err}")
                        batch_users = []

                except Exception as row_error:
                    errors += 1
                    if errors <= 3:  # Show first 3 errors
                        print(f"   Row {row_num}: Error processing user {row.get('user_id', 'unknown')}: {row_error}")

            # Commit remaining users
            if batch_users:
                db.add_all(batch_users)
                db.flush()
                print(f"   Committed final batch of {len(batch_users)} users")

        print(f"Users processing summary:")
        print(f"   Successfully prepared: {users_loaded} users")
        print(f"   Skipped/Errors: {errors}")

        db.commit()

def populate_tables():
    db: Session = SessionLocal()

    print("Populating tables from CSV...")
    
    # Check what's already loaded
    products_exist = db.query(Product).first() is not None
    users_exist = db.query(User).first() is not None
    orders_exist = db.query(Order).first() is not None
    order_items_exist = db.query(OrderItem).first() is not None
    
    if products_exist:
        print("Products already populated.")
    if users_exist:
        print("Users already populated.")
    if orders_exist:
        print("Orders already populated.")
    if order_items_exist:
        print("Order items already populated.")
        
    # Skip if everything is already loaded
    if products_exist and users_exist and orders_exist:
        print("All data already populated.")
        db.close()
        return

    try:
        # Load departments, aisles, products only if products don't exist
        if not products_exist:
            load_departments(db)
            load_aisles(db)
            load_products(db)

        # Load users only if they don't exist
        if not users_exist:
            load_users(db)

        if not orders_exist:
            load_orders(db)

        if not order_items_exist:
            load_order_items(db)

        # compute total_items per order after loading items
        print("Updating order totals...")
        order_item_counts = db.query(
            OrderItem.order_id, func.count(OrderItem.product_id)
        ).group_by(OrderItem.order_id).all()
        for order_id, total in order_item_counts:
            db.execute(
                update(Order).where(Order.id == order_id).values(total_items=total)
            )
        db.commit()

        print("Committing all changes to database...")
        db.commit()
        print("All CSV data successfully loaded into DB!")
        
        # Final verification
        final_products = db.query(Product).count()
        final_users = db.query(User).count()
        final_orders = db.query(Order).count()
        final_order_items = db.query(OrderItem).count()
        print(f"Final counts - Products: {final_products}, Users: {final_users},"
              f"Orders: {final_orders}, Order items: {final_order_items}")
        
        # Sample a few users to verify they loaded correctly
        sample_users = db.query(User).limit(3).all()
        if sample_users:
            print("Sample users in database:")
            for user in sample_users:
                print(f"   User {user.id} (external: {user.external_user_id}): {user.first_name} {user.last_name} ({user.email_address})")
        
    except Exception as e:
        print(f"CRITICAL ERROR during CSV loading: {e}")
        print("Full error details:")
        traceback.print_exc()
        try:
            db.rollback()
            print("Database rolled back successfully")
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
    finally:
        db.close()
