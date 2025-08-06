#!/usr/bin/env python3
"""
Simple ML Training Script for Time-LE
This script trains the ML models and saves them as persistent .pkl files.
"""

import sys
import os
sys.path.append('/app')
sys.path.append('/app/src')

from training.training import main as train_main

def main():
    """Run the training pipeline."""
    print("🚀 Starting ML model training for Time-LE...")
    print("📊 This will train Stage 1 (LightGBM) and Stage 2 (Gradient Boosting) models")
    print("💾 Models will be saved as .pkl files in /app/models/")
    print("=" * 60)
    
    try:
        # Run the training pipeline
        train_main()
        print("=" * 60)
        print("✅ Training completed successfully!")
        print("📁 Models saved to /app/models/")
        print("   - stage1_lgbm.pkl")
        print("   - stage2_gbc.pkl")
        print("🎯 You can now use these models for inference!")
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ Training failed: {e}")
        print("📋 Check the logs above for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()
