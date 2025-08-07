# TimeL-E: Predictive E-Commerce Platform
<p align ="center"> 
  <img width="512" height="512" alt="20250807_1721_Gradient Background Enhancement_remix_01k22ec3qtf589snrd7pgbp4wq" src="https://github.com/user-attachments/assets/50627919-beea-484a-8e26-f654ca6056dd" />
</p>
TimeL-E is an AI-powered e-commerce platform that uses machine learning to predict customer purchase behavior and provide personalized product recommendations. Built with a modern microservices architecture, it demonstrates the complete pipeline from data ingestion to intelligent user experiences. It is feature-rich, production minded, and designed for scalability and professionality. 

## Quick Start

Download dataset from Kaggle and put in data/: (File size too big for github)

https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis

Then Get the entire platform running with one command:

```bash
docker-compose up --build
```

**Access the Platform:**
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation Reccommended**: http://localhost:8000/docs
- **ML Service**: http://localhost:8001
- **Database Service**: http://localhost:7000

**Stop Everything:**
```bash
docker-compose down
```

## What TimeL-E Does

TimeL-E combines traditional e-commerce with an emphasis on engineering excellence with machine learning capabilities:

- **Smart Shopping Experience** - Users can browse products, manage carts, and place orders
- **Predictive Recommendations** - ML models analyze purchase history to suggest relevant products
- **Real-time Analytics** - Track user behavior and shopping patterns
- **Scalable Architecture** - Microservices design supports growth and customization

The platform is ideal for learning modern web development, exploring ML in production, or prototyping intelligent e-commerce features.

## Architecture

TimeL-E uses a microservices architecture with 5 main components:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │───▶│   Backend   │───▶│ DB Service  │
│ React + TS  │    │   FastAPI   │    │   FastAPI   │
│    :3000    │    │    :8000    │    │    :7000    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ ML Service  │    │ PostgreSQL  │
                   │   Python    │    │  Database   │
                   │    :8001    │    │    :5432    │
                   └─────────────┘    └─────────────┘
```

### Service Overview

| Service | Purpose | Technology |
|---------|---------|------------|
| **Frontend** | User interface and shopping experience | React, TypeScript, Tailwind CSS |
| **Backend** | API gateway and business logic | FastAPI, Python |
| **DB Service** | Database operations and user management | FastAPI, SQLAlchemy, PostgreSQL |
| **ML Service** | Product recommendations and predictions | Python, Scikit-learn, LightGBM |
| **Database** | Data storage and persistence | PostgreSQL |

## Team

**TimeL-E** is developed by:

- **Tal Weiss** – Backend Engineer & ML Engineer
- **Inbar Reshilovsky** – Frontend Engineer  
- **Anna Petrenko** – Data Systems Engineer

(We also did a lot of programming outside of our main roles)

## Documentation

This README provides a high-level overview. For detailed information about each component, see the specialized documentation:

### Development Guides
- **[Backend API Documentation](README_BACKEND.md)** - Complete API reference, endpoints, and development setup
- **[Frontend Development Guide](README_FRONTEND.md)** - React application, components, and UI development
- **[ML Training & Models](README_ML_TRAINING.md)** - Machine learning pipeline, model training, and predictions

### Infrastructure & Operations
- **[Docker Setup & Deployment](README_DOCKER.md)** - Complete containerization guide, from development to production
- **[Database Service](README_DB-SERVICE.md)** - Database operations, schema management, and data access

### Additional Resources
- **[Frontend API Documentation](FRONTEND_API_DOCUMENTATION.md)** - Frontend service integration details
- **[PgAdmin Guide](README_PGADMIN.md)** - Database administration interface

## Getting Started

1. **Clone the repository**
2. **Ensure Docker is installed** and running
3. **Run `docker-compose up --build`** to start all services
4. **Open http://localhost:3000** to access the application

For development work on specific components, consult the relevant documentation above for detailed setup instructions.

## License

This project is developed for educational and research purposes.





