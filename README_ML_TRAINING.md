# ML Training & Inference System - Time-LE

This document explains how to train and use the ML models in the Time-LE e-commerce system.

## 🎯 Overview

The ML system provides personalized product recommendations using a two-stage approach:
- **Stage 1**: LightGBM candidate generator (broader product selection)
- **Stage 2**: Gradient Boosting basket selector (refined recommendations)

## 📊 Current Status

✅ **Model Loading**: Pre-trained models load successfully  
✅ **Real Predictions**: Using actual ML inference (not mock data)  
✅ **Weighted Scores**: Real probability scores (0.1-0.9)  
✅ **Persistent Models**: Models saved as shareable `.pkl` files  
✅ **Docker Integration**: Full containerized training and inference  

## 🚀 How to Train Models

### Method 1: Simple Training Command (Recommended)
```bash
# Train new models (saves to persistent files)
docker-compose exec ml-service python train_models_optimized.py
```

### Method 2: Direct Training Script
```bash
# Alternative training approach
docker-compose exec ml-service python training/training.py
```

## 📁 Model Files

After training, models are saved as persistent files:
```
ml-service/models/
├── stage1_lgbm.pkl      # LightGBM candidate generator
├── stage2_gbc.pkl       # Gradient Boosting selector
└── (models persist across container restarts)
```

## 🔗 Git Integration

✅ **Shareable Models**: Trained models can be committed to Git  
✅ **No Retraining Needed**: Others can clone and use pre-trained models  
✅ **Version Control**: Track model changes over time  

```bash
# After training, commit models to Git
git add ml-service/models/stage1_lgbm.pkl
git add ml-service/models/stage2_gbc.pkl
git commit -m "Update trained ML models"
git push

# Someone else clones and gets working models
git clone <your-repo>
docker-compose up
# ✅ Inference works immediately!
```

## 🎯 How to Test Inference

### Check Model Status
```bash
curl http://localhost:8001/health | jq '.'
```

### Test Predictions
```bash
# Get ML predictions for a user (returns real weighted scores)
curl "http://localhost:8000/api/predictions/user/e18ddc09-37ba-5c3e-bff3-a2e8046c8249" | jq '.data.predictions[0:3]'
```

**Expected Output** (with real scores):
```json
[
  {
    "productId": 34126,
    "productName": "Organic Italian Parsley Bunch",
    "score": 0.85
  },
  {
    "productId": 22935,
    "productName": "Organic Yellow Onion",
    "score": 0.8
  },
  {
    "productId": 39984,
    "productName": "Organic Dill",
    "score": 0.7
  }
]
```

## 🔧 Technical Implementation

### Training Data Flow
```
CSV Files (./data/) → Docker Container → Feature Engineering → 
Train Models → Save .pkl files → Volume Persistence → 
Load for Inference → Real Weighted Predictions
```

### Docker Volume Configuration
- **Data Volume**: `./data:/app/training-data` (CSV data accessible)
- **Model Volume**: `./ml-service/models:/app/models` (persistent model storage)

### Key Improvements Made

1. **Fixed Model Loading**: Models now load actual trained weights
2. **Real Predictions**: Using trained model inference vs fallbacks
3. **Weighted Scores**: Probability-based scores vs fixed 0.8
4. **Persistent Files**: Models saved to local filesystem (Git-shareable)
5. **Simple Training**: One command to retrain models
6. **Docker Integration**: Full containerized workflow

## 🎉 Benefits

- ✅ **Real ML**: Actual trained model predictions
- ✅ **Weighted Scores**: Probability-based recommendation confidence
- ✅ **Easy Training**: Simple command to retrain models
- ✅ **Git Shareable**: Models can be version controlled and shared
- ✅ **No Database Dependency**: CSV-based training (simple)
- ✅ **Docker Ready**: Works in containerized environment

## 🛠 Troubleshooting

### Models Not Loading
```bash
# Check if models exist
docker-compose exec ml-service ls -la /app/models/

# Retrain if missing
docker-compose exec ml-service python train_models.py
```

### Training Fails
```bash
# Check logs
docker-compose logs ml-service

# Verify data exists
docker-compose exec ml-service ls -la /app/training-data/
```

### Predictions Return Fixed Scores
- Models may not be loaded properly
- Check ML service health endpoint
- Retrain models if necessary

---

**Ready to use!** The ML system now provides real personalized recommendations with proper weighted scores and persistent model files that can be shared via Git.
