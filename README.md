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

### 🔧 Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend

2. Install Packages:
    pip install -r ../requirements.txt

3. Start the server:
    uvicorn server:app --reload

