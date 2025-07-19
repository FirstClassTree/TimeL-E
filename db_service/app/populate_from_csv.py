import os
import csv
import traceback

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Product, Department, Aisle

CSV_DIR = "/data"

def populate_tables():
    db: Session = SessionLocal()

    # Skip if already populated
    if db.query(Product).first():
        print("Products already populated.")
        return

    print("Populating tables from CSV...")

    try:
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

        db.commit()
        print("CSV data loaded into DB.")
    except Exception as e:
        db.rollback()
        # print("Error populating tables:", e)
        traceback.print_exc()
    finally:
        db.close()
