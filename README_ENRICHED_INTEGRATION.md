# Enriched Product Data Integration

## Overview
This integration adds enriched product data (descriptions, prices, images) to the TimeL-E API endpoints. The enriched data is sourced from external APIs (OpenFoodFacts) and stored in the database for fast access.

## What's New

### **Enhanced API Responses**
All product endpoints now return enriched data:

```json
{
  "product_id": 1,
  "product_name": "Chocolate Sandwich Cookies",
  "aisle_id": 61,
  "department_id": 19,
  "aisle_name": "cookies cakes",
  "department_name": "snacks",
  "description": "Delicious chocolate sandwich cookies with cream filling",
  "price": 4.99,
  "image_url": "https://images.openfoodfacts.org/..."
}
```

### **Affected Endpoints**
- `GET /api/products/` - List products with enriched data
- `GET /api/products/search` - Search products with enriched data  
- `GET /api/products/{product_id}` - Individual product with enriched data
- All other product-related endpoints

### **Fallback Behavior**
Products without enriched data will have `null` values:
```json
{
  "product_id": 999,
  "product_name": "Some Product",
  "description": null,
  "price": null,
  "image_url": null
}
```

## Database Changes

### **New Table: `products.product_enriched`**
```sql
CREATE TABLE products.product_enriched (
    product_id integer PRIMARY KEY,
    description text,
    price numeric(10,2),
    image_url text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products.products(product_id)
);
```

### **Files Modified**
1. **Database Schema**: `database/schema.sql` - Added enriched table
2. **DB Service Models**: `db_service/app/models/products.py` - Added ProductEnriched model
3. **DB Service API**: `db_service/app/database_service.py` - Updated queries to include enriched data
4. **Backend Models**: `backend/app/models/grocery.py` - Added enriched fields to Product model
5. **Startup Script**: `db_service/app/main.py` - Auto-populate enriched data on startup

## Data Population

### **Automatic Population**
The enriched data is automatically populated when the db-service starts up. The system looks for `db_service/data/enriched_products_dept1.csv` and loads it into the database.

### **Manual Population**
If you need to manually populate or update enriched data:

```bash
# From the db_service directory
cd db_service
python -m app.populate_enriched_data
```

### **Generate New Enriched Data**
To create enriched data for all products:

```bash
# From the data directory
cd data
python product_enricher.py
# Then restart services
```

## Development

### **Testing API Changes**
Test the enriched data endpoints:

```bash
# List products with enriched data
curl http://localhost:8000/api/products/

# Search products with enriched data
curl "http://localhost:8000/api/products/search?q=chocolate"

# Get specific product with enriched data
curl http://localhost:8000/api/products/1
```

### **Database Migration**
If you have an existing database, run the migration script:

```sql
-- From PostgreSQL or pgAdmin
\i db_service/update_schema.sql
```

### **Regenerating Enriched Data**
1. Run the enricher script: `python product_enricher.py`
2. Restart the db-service or run the populate script manually

## Performance

### **Query Performance**
- Enriched data is joined using LEFT JOIN (no impact on non-enriched products)
- Database indexes on `product_id` ensure fast lookups
- Eager loading prevents N+1 query problems

### **Data Volume**
- Currently all 49,000+ products across all departments have enriched data
- Each enriched record adds ~200 bytes (description + image URL)
- Total additional storage: ~10MB for the full dataset

## Future Enhancements

1. **Data Refresh**: Scheduled updates of enriched data
2. **Cache Layer**: Redis caching for frequently accessed products
3. **Image Optimization**: Thumbnail generation and CDN integration
4. **Price Updates**: Real-time price synchronization

## Troubleshooting

### **No Enriched Data Showing**
1. Ensure the enriched CSV file exists, for example: `data/enriched_products_dept1.csv`
2. Verify the database table has been created and populated:  
`SELECT COUNT(*) FROM products.product_enriched;`
3. Review db-service logs for any errors during data population.

### **Database Errors**
1. Make sure the database schema is up to date
2. Run the migration script: `db_service/update_schema.sql`
3. Check foreign key constraints are satisfied

### **API Returns 500 Errors**
1. Check db-service is running and healthy
2. Verify database connection is working
3. Check backend logs for specific error messages

## Data Sources

- **Descriptions**: OpenFoodFacts API (crowd-sourced food database)
- **Prices**: Generated random values ($1.00 - $15.00)
- **Images**: OpenFoodFacts product images or placeholder images
- **Fallbacks**: Generated descriptions for products not found in API

---

This integration enhances the TimeL-E platform with rich product information  
while maintaining backward compatibility and performance.

