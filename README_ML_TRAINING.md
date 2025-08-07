# ML Training & Recommendations

Machine learning system for TimeL-E that provides personalized product recommendations using a two-stage approach with LightGBM and Gradient Boosting models.

## Overview

The ML system analyzes user purchase history to predict what products they're likely to buy next. It uses a stacked model approach:

- **Stage 1**: LightGBM generates candidate products from the entire catalog
- **Stage 2**: Gradient Boosting ranks and selects the final recommendations

Models are trained on CSV data from the `/data` directory and saved as `.pkl` files that persist across container restarts.

## Training Models

### Quick Start
Train new models with the optimized script (Still takes around 5 hours):
```bash
docker-compose exec ml-service python train_models_optimized.py
```

### Alternative Training (Quick)
Use the basic training script:
```bash
docker-compose exec ml-service python train_models_debug.py
```

### Training Process
The training pipeline:
1. Loads CSV data from `/app/training-data` (mounted from `./data`)
2. Generates features for users and products
3. Trains Stage 1 LightGBM model for candidate generation
4. Trains Stage 2 Gradient Boosting model for final ranking
5. Saves models to `/app/models` (mounted from `./ml-service/models`)

## Model Files

After training, you'll find these files:
```
ml-service/models/
├── stage1_lgbm.pkl      # LightGBM candidate generator
├── stage2_gbc.pkl       # Gradient Boosting selector
└── stage1_lgbm-1.pkl    # Backup/versioned models
```

These files are part of your local filesystem and can be committed to Git for sharing.

## Using the Models

### Check Model Status
```bash
curl http://localhost:8001/health
```

### Get Recommendations
```bash
# Get predictions for a specific user
curl "http://localhost:8000/api/predictions/user/e18ddc09-37ba-5c3e-bff3-a2e8046c8249"
```

Example response:
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "productId": 34126,
        "productName": "Organic Italian Parsley Bunch",
        "score": 0.85
      },
      {
        "productId": 22935, 
        "productName": "Organic Yellow Onion",
        "score": 0.78
      }
    ]
  }
}
```

## Architecture

### Data Flow
```
CSV Files → Feature Engineering → Train Models → Save .pkl → Load for Inference → API Predictions
```

### Feature Engineering
The system generates these features:
- **Product features**: Category, popularity, pricing patterns
- **User features**: Purchase frequency, category preferences, seasonality  
- **User-product features**: Past interactions, time since last purchase

### Memory Optimization
The optimized trainer uses chunked processing to handle large datasets without running out of memory.

## Development

### Model Development Cycle
1. Modify features or model parameters in the training scripts
2. Run training to generate new models
3. Test predictions via the API
4. Commit working models to version control

### Training Data Requirements
The system expects these CSV files in the `/data` directory:
- `orders_demo.csv` - Order history
- `order_items_demo.csv` - Order line items  
- `products.csv` - Product catalog
- `users_demo_v2.csv` - User information

### Adding New Features
Feature engineering happens in:
- `ChunkedFeatureEngineer` class in `train_models_optimized.py`
- `src/features/engineering.py` for more complex features

### Model Configuration
Key parameters can be adjusted in the training scripts:
- `chunk_size` - Memory usage vs speed tradeoff
- LightGBM parameters - Learning rate, depth, regularization
- Gradient Boosting parameters - Estimators, learning rate

## Troubleshooting

### Models not loading
Check if model files exist:
```bash
docker-compose exec ml-service ls -la /app/models/
```

If missing, retrain:
```bash
docker-compose exec ml-service python train_models_optimized.py
```

### Training fails with memory errors
The optimized trainer should handle large datasets, but you can:
- Reduce `chunk_size` in the training script
- Use a subset of data for initial development
- Monitor memory usage with `docker stats`

### Predictions return low-quality results
- Ensure you have enough training data (at least a few months of orders)
- Check that user has purchase history in the training data
- Verify feature engineering is working correctly

### Performance Issues
- Check if models are properly loaded (not falling back to random recommendations)
- Monitor ML service logs for warnings
- Consider retraining if data distribution has changed significantly

## File Structure

```
ml-service/
├── simple_model_wrapper.py    # Model inference wrapper
├── train_models.py            # Basic training script  
├── train_models_optimized.py  # Memory-optimized training
├── models/                    # Saved model files (.pkl)
├── src/
│   ├── api/main.py           # FastAPI service
│   └── features/             # Feature engineering
└── training/                 # Training utilities
```

The ML service runs on port 8001 and provides a `/predict` endpoint that the backend calls for recommendations.
