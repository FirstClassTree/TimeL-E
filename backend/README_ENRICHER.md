# Product Enricher Script

## Overview
This standalone Python script enriches product data from `products.csv` by calling external APIs to get descriptions, prices, and image URLs. It processes products incrementally by department to manage API load and processing time.

## Features
- ✅ **Department-based filtering** - Process one department at a time
- ✅ **OpenFoodFacts API integration** - Free grocery product database
- ✅ **Progress tracking** - Shows processing status
- ✅ **Error handling** - Continues processing even if some API calls fail
- ✅ **Fallback data** - Generates reasonable defaults when API fails
- ✅ **Respectful API usage** - Built-in delays between requests

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r enricher_requirements.txt
```

### 2. Run the Script
```bash
python product_enricher.py
```

### 3. Check Results
The script will create: `data/enriched_products_dept1.csv`

## Configuration

Edit these variables in `product_enricher.py`:

```python
DEPARTMENT_ID = 1           # Change to process different departments
API_DELAY = 0.5            # Seconds between API calls
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

```csv
product_id,product_name,description,price,image_url
1,Chocolate Sandwich Cookies,"Delicious chocolate sandwich cookies",4.99,https://...
2,All-Seasons Salt,"Premium all-purpose seasoning salt",2.34,https://...
```

## Processing Different Departments

To process other departments:

1. Change `DEPARTMENT_ID = 2` (or any department number)
2. Run the script again
3. Output will be saved as `enriched_products_dept2.csv`

## Estimated Processing Time

- **Department 1**: ~2-5 minutes (depending on product count)
- **Small departments**: 1-2 minutes
- **Large departments**: 5-10 minutes

## API Information

- **API Used**: OpenFoodFacts (https://world.openfoodfacts.org/)
- **Rate Limiting**: 0.5 seconds between requests
- **No API Key Required**: Free public API
- **Fallback**: If API fails, generates reasonable default data

## Troubleshooting

### "Input file not found"
Make sure you're running the script from the `backend/` directory:
```bash
cd backend
python product_enricher.py
```

### "No products found for department_id"
Check what departments exist in your data:
```python
import pandas as pd
df = pd.read_csv('../data/products.csv')
print(df['department_id'].unique())
```

### Slow processing
- Reduce `API_DELAY` (but be respectful to the API)
- Process smaller departments first
- Check your internet connection

## Sample Log Output

```
🛒 TimeL-E Product Enricher
========================================
Processing department: 1
Input file: ../data/products.csv
Output file: ../data/enriched_products_dept1.csv
API delay: 0.5s between requests
========================================

2025-07-18 12:57:00,123 - INFO - Reading products from ../data/products.csv
2025-07-18 12:57:00,124 - INFO - Found 456 products in department 1
2025-07-18 12:57:00,125 - INFO - Processing 1/456: Chocolate Sandwich Cookies
2025-07-18 12:57:01,234 - INFO - Processing 2/456: All-Seasons Salt
...
2025-07-18 13:02:15,789 - INFO - ✅ Successfully saved 456 enriched products to ../data/enriched_products_dept1.csv

✅ Processing completed in 315.2 seconds
📁 Results saved to: ../data/enriched_products_dept1.csv

💡 To process other departments, change DEPARTMENT_ID and run again
