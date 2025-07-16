# TimeL-E Grocery Frontend

A domain-specific backend API for the TimeL-E grocery e-commerce application, built around real CSV data structures and designed for frontend integration.

## Architecture

This backend serves as a **Grocery-Focused API** that:
- ✅ Serves real grocery data based on CSV file structure
- ✅ Provides domain-specific endpoints (products, orders, categories)
- ✅ Includes smart product search and filtering
- ✅ Handles order management with product validation
- ✅ Offers category navigation (departments & aisles)
- ✅ Returns frontend-ready responses with joined data

## Project Structure

```
frontend/
├── src/
│   ├── stores/              # Main components
│   │   ├── App.tsx
│   │   ├── index.css        # Custom font imports and variables
│   │   └── main.tsx         # App initialization
│   ├── pages/               # All possible pages in main app and admin
│   │   ├── Cart.tsx
│   │   ├── Checkout.tsx
│   │   ├── ForgotPassword.tsx
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── OrderDetail.tsx
│   │   ├── Orders.tsx
│   │   ├── PredictedBasket.tsx
│   │   ├── ProductDetail.tsx
│   │   ├── Products.tsx
│   │   ├── Profile.tsx
│   │   ├── Register.tsx
│   │   ├── ResetPassword.tsx
│   │   └──admin/
│   │      ├── Dashboard.tsx
│   │      ├── DemoPredictionPage.tsx
│   │      ├── Metrics.tsx
│   │      ├── Orders.tsx
│   │      ├── Products.tsx
│   │      ├── Settings.tsx
│   │      ├── Users.tsx
│   │      └── UserSeeding.tsx
│   ├── layouts/             # All possible pages in main app and admin
│   │   ├── AdminLayout.tsx
│   │   ├── AuthLayout.tsx
│   │   └── MainLayout.tsx
│   ├── components/          # Diffrent components used in pages
│   │   ├── admin/
│   │   │   ├─ DateRangePicker.tsx
│   │   │   ├─ MetricCard.tsx
│   │   │   └─ MetricExplanation.tsx
│   │   ├── auth/
│   │   │   ├─ AdminRoute.tsx
│   │   │   └─ ProtectedRoute.tsx
│   │   ├── cart/
│   │   │   └─ CartDropdown.tsx
│   │   ├── common/
│   │   │   ├─ EmptyState.tsx
│   │   │   ├─ ErrorBoundary.tsx
│   │   │   ├─ LoadingSpinner.tsx
│   │   │   └─ Pagination.tsx
│   │   ├── home/
│   │   │   ├─ FeatureCard.tsx
│   │   │   └─ Hero.tsx
│   │   ├── navigation/
│   │   │   └─ MobileMenu.tsx
│   │   ├── notifications/
│   │   │   └─ NotificationDropdown.tsx
│   │   ├── predictions/
│   │   │   ├─ ConfidenceIndicator.tsx
│   │   │   └─ PredictionExplanation.tsx
│   │   ├── products/
│   │   │   ├─ CategoryFilter.tsx
│   │   │   ├─ PriceRangeFilter.tsx
│   │   │   ├─ ProductCard.tsx
│   │   │   ├─ ProductImage.tsx
│   │   │   ├─ ProductListItem.tsx
│   │   │   └─ SortDropdown.tsx
│   │   └── search/
│   │       └─ SearchModal.tsx
│   └── services/                # APIs
│       ├── admin.service.ts
│       ├── api.client.ts
│       ├── auth.service.ts
│       ├── cart.service.ts
│       ├── order.service.ts
│       ├── prediction.service.ts
│       ├── product.service.ts
│       └── user.service.ts
├── Dockerfile               # Container configuration
├── postcss.config.js        # postcss configuration
├── tailwind.config.js       # tailwind configuration
├── vite.config.ts           # vite configuration
└── requirements.txt         # Python dependencies
```

## 🚀 Deployment Instructions

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for ML development)
- Git

### Quick Start with Docker

1. **Build and Start All Services**:
   ```bash
   docker-compose up --build -d
   cd frontend
   npm install
   npm audit fix --force
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npm run dev
   ```

2**Access the Application**:
   - Frontend: http://localhost:3000
   - Admin Dashboard: http://localhost:3000/admin

### Default Credentials

- **Admin Account**:
  - Email: admin@timely.com
  - Password: password

- **Test User Account**:
  - Email: test@timely.com
  - Password: password


The TimeL-E Grocery API provides a solid foundation for your e-commerce platform with realistic data structures and comprehensive functionality for managing products, orders, and categories.
