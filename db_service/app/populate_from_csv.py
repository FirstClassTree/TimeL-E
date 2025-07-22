import os
import csv
import traceback

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Product, Department, Aisle
from app.models.users import User

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
            with open(os.path.join(CSV_DIR, "departments.csv"), newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(Department(
                        department_id=int(row["department_id"]),
                        department=row["department"]
                    ))

            # Load aisles
            with open(os.path.join(CSV_DIR, "aisles.csv"), newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(Aisle(
                        aisle_id=int(row["aisle_id"]),
                        aisle=row["aisle"]
                    ))

            # Load products
            with open(os.path.join(CSV_DIR, "products.csv"), newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(Product(
                        product_id=int(row["product_id"]),
                        product_name=row["product_name"],
                        aisle_id=int(row["aisle_id"]),
                        department_id=int(row["department_id"])
                    ))

        # Load users only if they don't exist
        if not users_exist:
            users_file = os.path.join(CSV_DIR, "users_demo.csv")
            print(f"👥 Loading users from: {users_file}")
            
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
                            existing_name = db.query(User).filter(User.name == row['name']).first()
                            existing_email = db.query(User).filter(User.email_address == row['email_address']).first()
                            
                            if existing_user_id:
                                if errors < 3:
                                    print(f"   Row {row_num}: User ID {row['user_id']} already exists, skipping")
                                errors += 1
                                continue
                            
                            if existing_name:
                                if errors < 3:
                                    print(f"   Row {row_num}: User name '{row['name']}' already exists, skipping")
                                errors += 1
                                continue
                                
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
                                db.add_all(batch_users)
                                db.flush()  # Flush to catch constraint errors
                                print(f"   Committed batch of {len(batch_users)} users")
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
