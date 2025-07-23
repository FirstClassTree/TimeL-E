import os
import csv
import traceback

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db_core.database import SessionLocal
from app.db_core.models import Product, Department, Aisle, User

CSV_DIR = "/data"

def populate_tables():
    db: Session = SessionLocal()

    print("Populating tables from CSV...")
    
    # Check what's already loaded
    products_exist = db.query(Product).first() is not None
    users_exist = db.query(User).first() is not None
    
    if products_exist:
        print("Products already populated.")
    if users_exist:
        print("Users already populated.")
        
    # Skip if everything is already loaded
    if products_exist and users_exist:
        print("All data already populated.")
        db.close()
        return

    try:
        # Load departments, aisles, products only if products don't exist
        if not products_exist:
            # Load departments
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

            # Load aisles
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

            # Load products
            products_file = os.path.join(CSV_DIR, "products.csv")
            print(f"Loading products from: {products_file}")
            batch_size = 200  # Tweak as needed
            batch_products = []
            products_loaded = 0
            product_errors = 0
            success_count = 0
            with open(products_file, newline='') as f:
                reader = csv.DictReader(f)
                # for row in reader:
                #     db.add(Product(
                #         product_id=int(row["product_id"]),
                #         product_name=row["product_name"],
                #         aisle_id=int(row["aisle_id"]),
                #         department_id=int(row["department_id"])
                #     ))

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
                                if  success_count % 10000 == 0:
                                    print(f"   Committed batch of {len(batch_products)} products")
                                batch_products = []
                            except (IntegrityError, SQLAlchemyError) as batch_err:
                                db.rollback()
                                print(
                                    f"   ERROR: Batch insert failed at row {row_num} (will try individually): {batch_err}")
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

                # Commit any remaining products in the final batch
                if batch_products:
                    try:
                        db.add_all(batch_products)
                        db.flush()
                        print(f"   Committed final batch of {len(batch_products)} products")
                    except (IntegrityError, SQLAlchemyError) as batch_err:
                        db.rollback()
                        print(f"   ERROR: Final batch insert failed (will try individually): {batch_err}")
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

        # Load users only if they don't exist
        if not users_exist:
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
                
                users_loaded = 0
                errors = 0
                batch_size = 100
                
                with open(users_file, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    print(f"CSV columns: {reader.fieldnames}")
                    
                    batch_users = []
                    for row_num, row in enumerate(reader, 1):
                        try:
                            # Check for unique constraint violations before adding
                            existing_user_id = db.query(User).filter(User.user_id == int(row['user_id'])).first()
                            # existing_name = db.query(User).filter(User.name == row['name']).first()
                            existing_email = db.query(User).filter(User.email_address == row['email_address']).first()
                            
                            if existing_user_id:
                                if errors < 3:
                                    print(f"   Row {row_num}: User ID {row['user_id']} already exists, skipping")
                                errors += 1
                                continue
                            
                            # if existing_name:
                            #     if errors < 3:
                            #         print(f"   Row {row_num}: User name '{row['name']}' already exists, skipping")
                            #     errors += 1
                            #     continue
                                
                            if existing_email:
                                if errors < 3:
                                    print(f"   Row {row_num}: Email '{row['email_address']}' already exists, skipping")
                                errors += 1
                                continue
                            
                            user = User(
                                user_id=int(row['user_id']),
                                name=row['name'],
                                hashed_password=row['hashed_password'],
                                email_address=row['email_address'],
                                phone_number=row['phone_number'],
                                street_address=row['street_address'],
                                city=row['city'],
                                postal_code=row['postal_code'],
                                country=row['country']
                            )
                            batch_users.append(user)
                            users_loaded += 1
                            
                            if users_loaded <= 5:  # Show first 5 for confirmation
                                print(f"   Row {row_num}: Prepared user {row['user_id']}: {row['name']}")
                            
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

        print("Committing all changes to database...")
        db.commit()
        print("All CSV data successfully loaded into DB!")
        
        # Final verification
        final_products = db.query(Product).count()
        final_users = db.query(User).count()
        print(f"Final counts - Products: {final_products}, Users: {final_users}")
        
        # Sample a few users to verify they loaded correctly
        sample_users = db.query(User).limit(3).all()
        if sample_users:
            print("Sample users in database:")
            for user in sample_users:
                print(f"   User {user.user_id}: {user.name} ({user.email_address})")
        
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
