# Static Images

This directory contains static images served by the frontend.

## Setup Required
**IMPORTANT**: To see default product images, copy the image file:

```bash
cp frontend/storage/image_not_available.png frontend/public/storage/image_not_available.png
```

## How it works
The ProductImage component will:
1. Try to load the actual product image
2. If null/empty, try to load `/storage/image_not_available.png` (local image)
3. If that fails, fall back to `https://via.placeholder.com/300x300?text=No+Image` (external placeholder)

## Current Status
- ✅ ProductImage component updated with fallback logic
- ✅ Product service fixed to pass all filter parameters
- ⚠️  **Manual action needed**: Copy the image file to see default images
