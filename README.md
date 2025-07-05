# 🛒 TimeL - E: Predictive Shopping Cart System

**TimeL - E** is a prototype e-commerce analytics platform that leverages historical shopping cart data to predict future cart contents using machine learning. Built for rapid iteration and educational purposes, it showcases a full-stack pipeline including data ingestion, model training, API deployment, and frontend interaction.
---

## 👥 Team Members

- **Tal Weiss** – Backend Engineer  
- **Inbar Reshilovsky** – Frontend Engineer  
- **Ohad Libai** – ML Engineer  
- **Anna Petrenko** – Data Engineer  

---

## 📦 Project Structure
```
timele-project/
├── backend/ # FastAPI server and Database Managing
├── frontend/ # UI (React or Streamlit)
├── ml/ # Data processing and model training
├── data/ # Input and sample data
├── database/ # DB schema scripts
└── README.md
```


## ⚙️ Setup and Run

Follow these steps to get the full TimeL - E stack running locally.

## Install from Kaggle and put in Data/
https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis

### 🔧 Backend (Python FastAPI)

**Option 1: Docker (Recommended)**
```bash
docker-compose up --build
```

**Option 2: Local Development**
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install packages:
   ```bash
   pip install -r ../requirements.txt
   ```

3. Start the server:
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload
   ```

4. Access the API:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs (Explanation of API endpoints)
   - Health Check: http://localhost:8000/health

**Backend Features:**
- 📦 Product search and filtering based on CSV data
- 🛒 Order management with product validation
- 📋 Category navigation (departments & aisles)
- 🔍 Smart product search functionality
- 🔗 Coordinates frontend, database, and ML services
- 📖 Auto-generated API documentation

> See [README_BACKEND.md](README_BACKEND.md) for detailed backend documentation.
