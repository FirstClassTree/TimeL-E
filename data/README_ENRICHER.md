# Product Enricher Script

## Overview
This standalone Python script enriches product data from `products.csv` by calling external APIs to get  
descriptions, prices, and image URLs. It processes products incrementally by department to manage API load  
and processing time.

> All output CSVs will be saved in the products_enriched/ subdirectory.

## Features
- **Department-based filtering** - Choose to process a single department with `--department` or all departments at once (auto-detected from departments.csv)
- **OpenFoodFacts API integration** - Free grocery product database
- **Progress tracking** - Shows processing status
- **Error handling** - Continues processing even if some API calls fail
- **Fallback data** - Generates reasonable defaults when API fails
- **Respectful API usage** - Built-in delays between requests

## Quick Start

### 1. Install Dependencies
```bash
cd data
pip3 install -r enricher_requirements.txt
```

### 2. Run the Script
To process **all departments**:
```bash
python3 product_enricher.py
```

To process a **single department** (for example, department 3):
```bash
python3 product_enricher.py --department 3
```

### 3. Check Results
The script will create one CSV file per department inside `products_enriched/`, for example:  
`products_enriched/enriched_products_dept1.csv`, `products_enriched/enriched_products_dept2.csv`, etc.

When processing a single department, the output will be:   
`products_enriched/enriched_products_dept{DEPARTMENT_ID}.csv`

## Configuration

Edit these variables in `product_enricher.py`:

```python
REQUESTS_PER_SECOND = 10   # API rate limit (requests per second)
TIMEOUT = 10               # Request timeout in seconds
```

## Output Format

The enriched CSV contains:
- `product_id` - Original product ID
- `product_name` - Original product name  
- `description` - Product description from API or generated
- `price` - Random price between $1.00-$15.00
- `image_url` - Product image URL or placeholder

## Example Output


| product_id | product_name               | description                          | price | image_url       |
|------------|----------------------------|--------------------------------------|-------|-----------------|
| 1          | Chocolate Sandwich Cookies | Delicious chocolate sandwich cookies | 4.99  | https://...     |
| 2          | All-Seasons Salt           | Premium all-purpose seasoning salt   | 2.34  | https://...     |


## Processing Different Departments

To process a specific department, use the `--department` argument:

```bash
python3 product_enricher.py --department 2
```
To process all departments at once, simply run:

```bash
python3 product_enricher.py
```

## Estimated Processing Time

- **Typical (Department 1)**: ~2-5 minutes (depending on product count)
- **Small departments**: 1-2 minutes
- **Large departments**: 5-10 minutes

## API Information

- **API Used**: OpenFoodFacts (https://world.openfoodfacts.org/)
- **Rate Limiting**: Configurable with REQUESTS_PER_SECOND (default: 0.1 seconds between requests)
- **No API Key Required**: Free public API
- **Fallback**: If API fails, reasonable default data is generated

## Troubleshooting

### "Input file not found"
Ensure the script is executed from the `data/` directory:
```bash
cd data
python product_enricher.py
```

### "No products found for department_id"
To check which departments are present in the data:
```python
import pandas as pd
df = pd.read_csv('products.csv')
print(df['department_id'].unique())
```

### Slow processing
- Lower the `REQUESTS_PER_SECOND` value in the script to be even more respectful to the API
- Process smaller departments first
- Check network connection

## Sample Log Output

for `python3 product_enricher.py -d 2`

```
🛒 TimeL-E Product Enricher (Concurrent Version)
==================================================
Processing departments: [2]
Input file: products.csv
Output files:
  products_enriched/enriched_products_dept2.csv
Concurrent workers: 15
Rate limit: 10 requests/second
==================================================

--- Processing department 2 ---
2025-07-22 02:58:36,651 - INFO - Reading products from products.csv
2025-07-22 02:58:36,685 - INFO - Found 548 products in department 2
2025-07-22 02:58:36,685 - INFO - Using 15 concurrent workers for processing
2025-07-22 02:58:36,685 - INFO - Rate limit: 10 requests per second
2025-07-22 02:58:38,180 - INFO - Progress: 10/548 products processed
...
2025-07-22 02:59:31,183 - INFO - Progress: 540/548 products processed
2025-07-22 02:59:32,169 - INFO - Progress: 548/548 products processed
2025-07-22 02:59:32,169 - INFO - ✅ Successfully saved 548 enriched products to products_enriched/enriched_products_dept2.csv
2025-07-22 02:59:32,169 - INFO -
============================================================
2025-07-22 02:59:32,169 - INFO - SAMPLE RESULTS (first 3 products):
2025-07-22 02:59:32,169 - INFO - ============================================================
2025-07-22 02:59:32,169 - INFO -
Product 1:
2025-07-22 02:59:32,169 - INFO -   ID: 86
2025-07-22 02:59:32,169 - INFO -   Name: Camilia, Single Liquid Doses
2025-07-22 02:59:32,169 - INFO -   Description: Quality camilia, single liquid doses - fresh grocery product...
2025-07-22 02:59:32,169 - INFO -   Price: $5.97
2025-07-22 02:59:32,169 - INFO -   Image: https://via.placeholder.com/300x300?text=No+Image...
2025-07-22 02:59:32,169 - INFO -
Product 2:
2025-07-22 02:59:32,169 - INFO -   ID: 506
2025-07-22 02:59:32,169 - INFO -   Name: Arrowroot Powder
2025-07-22 02:59:32,169 - INFO -   Description: Arrowroot powder...
2025-07-22 02:59:32,169 - INFO -   Price: $7.08
2025-07-22 02:59:32,169 - INFO -   Image: https://images.openfoodfacts.org/images/products/0...
2025-07-22 02:59:32,169 - INFO -
Product 3:
2025-07-22 02:59:32,169 - INFO -   ID: 535
2025-07-22 02:59:32,169 - INFO -   Name: Rescue Remedy
2025-07-22 02:59:32,169 - INFO -   Description: Bach Rescue Remedy...
2025-07-22 02:59:32,169 - INFO -   Price: $6.31
2025-07-22 02:59:32,169 - INFO -   Image: https://images.openfoodfacts.org/images/products/0...
2025-07-22 02:59:32,169 - INFO -
📊 SUMMARY:
2025-07-22 02:59:32,169 - INFO -    Total products processed: 548
2025-07-22 02:59:32,169 - INFO -    Department: 2
2025-07-22 02:59:32,169 - INFO -    Output file: products_enriched/enriched_products_dept2.csv
2025-07-22 02:59:32,169 - INFO -    Average price: $8.07

✅ Department 2 completed in 55.5 seconds
📁 Results saved to: products_enriched/enriched_products_dept2.csv
⚡ Speed: ~9.9 products/second

=== ALL PROCESSING COMPLETE ===
Total time: 55.5 seconds
```
