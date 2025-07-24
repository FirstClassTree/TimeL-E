# Static Images

This directory contains static images served by the frontend.

## Setup
Copy `frontend/storage/image_not_available.png` to this directory for the default product image to work properly.

The ProductImage component will:
1. Try to load the actual product image
2. If null/empty, try to load `/storage/image_not_available.png`
3. If that fails, fall back to `https://via.placeholder.com/300x300?text=No+Image`
