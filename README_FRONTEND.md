# TimeL-E Frontend

Modern React application for the TimeL-E predictive e-commerce platform. Built with TypeScript, Tailwind CSS, and AI-powered features for intelligent grocery shopping.

## Try the Demo

Experience TimeL-E instantly without registration:

**Quick Demo**
- Click the "Demo User" button on the login page for instant access

**Full Demo Login**
- Email: `user43682@timele-demo.com`
- Password: `password`

Demo users have pre-loaded shopping history that showcases AI predictions immediately.

## Key Features

### AI-Powered Shopping
- **Predicted Baskets** - ML-generated weekly shopping recommendations
- **Confidence Scores** - Visual indicators showing prediction accuracy

### Modern Shopping Experience  
- **Advanced Search** - Real-time product search with filtering
- **Smart Filtering** - Filter by departments, price ranges, categories
- **Multiple Views** - Grid and list layouts with smooth animations
- **Persistent Cart** - Shopping cart maintained across sessions
- **Responsive Design** - Optimized for desktop, tablet, and mobile

### Professional UI/UX
- **Dark Mode** - Complete light/dark theme support
- **Smooth Animations** - Framer Motion micro-interactions
- **Loading States** - Professional skeleton screens and indicators
- **Error Handling** - Graceful error boundaries and user feedback

## Application Pages:

### Core Shopping Experience
- **Home** - Modern landing page with hero section and AI prediction access
- **Products** - Advanced catalog with search, filtering, and sorting
- **ProductDetail** - Individual product pages with detailed information
- **PredictedBasket** - AI-powered weekly shopping recommendations
- **Cart** - Shopping cart with quantity management and price calculations
- **Checkout** - Secure checkout process with payment integration

### User Authentication & Account
- **Login** - User authentication with demo access options
- **Register** - New user registration
- **ForgotPassword** - Password recovery process
- **ResetPassword** - Password reset functionality
- **Profile** - User profile management and preferences

### Order Management
- **Orders** - Complete order history and tracking
- **OrderDetail** - Detailed view of individual orders
- **NotificationSettings** - Customizable shopping reminders and alerts

## Technology Stack

- **React 18** + **TypeScript** - Modern React development
- **Vite** - Fast development and optimized builds
- **Tailwind CSS** - Utility-first styling framework
- **Zustand** - Lightweight state management
- **TanStack Query** - Data fetching and caching
- **Framer Motion** - Smooth animations
- **React Hook Form** - Form handling and validation

## Quick Start

Start the application with Docker:
```bash
# Start all services
docker-compose up --build

# Access the frontend
# http://localhost:3000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── auth/           # Authentication components  
│   │   ├── cart/           # Shopping cart components
│   │   ├── home/           # Homepage components
│   │   ├── predictions/    # AI prediction components
│   │   ├── products/       # Product components
│   │   └── common/         # Shared components
│   ├── pages/              # Application pages
│   │   ├── Home.tsx        # Landing page
│   │   ├── Products.tsx    # Product catalog
│   │   ├── PredictedBasket.tsx # AI recommendations
│   │   ├── Cart.tsx        # Shopping cart
│   │   └── [other pages]
│   ├── services/           # API services
│   │   ├── auth.service.ts
│   │   ├── cart.service.ts
│   │   ├── product.service.ts
│   │   └── prediction.service.ts
│   ├── stores/             # State management
│   │   ├── auth.store.ts
│   │   └── cart.store.ts
│   └── layouts/            # Page layouts
├── Dockerfile              # Container configuration
├── tailwind.config.js      # Tailwind configuration
└── vite.config.ts          # Vite configuration
```

## Development

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production  
npm run build
```

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000/api
```

## Features in Detail

### AI Integration
The frontend seamlessly integrates with the ML service to provide intelligent shopping recommendations. Users can view prediction confidence scores, understand recommendation reasoning, and provide feedback to improve future predictions.

### State Management
Uses Zustand for global state management with separate stores for authentication, shopping cart, and UI state. TanStack Query handles server state with intelligent caching and background updates.

### Responsive Design
Built mobile-first with Tailwind CSS. Components adapt fluidly across device sizes with touch-friendly interactions and optimized layouts for different screen sizes.

### Performance
Implements code splitting, lazy loading, optimistic updates, and intelligent caching for fast, responsive user experience.

The frontend demonstrates modern React development practices while showcasing AI-powered e-commerce capabilities in an intuitive, professional interface.
