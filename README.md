# 🚀 Equipment Failure Prediction Platform

### Real-Time Data Pipeline | Feature Engineering | Machine Learning | Batch Scoring | Docker + PostgreSQL

This project is a **full end-to-end equipment monitoring and failure prediction pipeline**.
It simulates equipment sensor readings, processes raw data, loads it into a data warehouse, trains an ML model, and generates failure-risk predictions for operational use.

It demonstrates practical skills in:

* **Data Engineering** (Pipelines, ETL, Data Lake, Warehousing)
* **Machine Learning** (Feature Engineering, Model Training, Scoring)
* **Software Engineering** (Modular project structure, reproducible code)
* **DevOps** (Docker, Docker Compose, Dependency Management)
* **Analytics** (Exploratory Data Analysis, Data Visualization)
* **PostgreSQL** (Schemas, Constraints, Fact Tables, UPSERTS)

This repository is perfect for **internships, ML/DE job applications, and showcasing real-world portfolio work**.

---

# 📊 Project Architecture

```
                ┌───────────────────────────┐
                │  Synthetic Sensor Data     │
                │  (generate_synthetic_data) │
                └───────────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────┐
                     │   Data Lake      │
                     │ raw / processed  │
                     └──────────┬───────┘
                                │
                ┌───────────────┴──────────────────┐
                ▼                                  ▼
      transform_raw_to_processed.py       train_failure_model.py
            (clean + engineer)            (ML training + artifacts)
                                │
                                ▼
                   load_processed_to_warehouse.py
                     (PostgreSQL fact tables)
                                │
                                ▼
                     batch_score_latest_readings.py
               (Apply ML model → failure risk scores)
                                │
                                ▼
               PostgreSQL Warehouse (Docker + Adminer)
```

---

# 📁 Folder Structure

```
equipment-failure-prediction/
│
├── data_lake/
│   ├── raw/                   # Raw sensor CSVs
│   └── processed/             # Cleaned + engineered files
│
├── db/
│   ├── init.sql               # Schema + constraints
│   └── seed_machines.sql      # Machine dimension data
│
├── ingestion/
│   └── generate_synthetic_data.py
│
├── ml/
│   ├── train_failure_model.py
│   └── batch_score_latest_readings.py
│
├── models/
│   └── failure_model_rf_v1.pkl
│
├── notebooks/
│   └── 01_eda_and_baseline_model.ipynb
│
├── pipelines/
│   ├── transform_raw_to_processed.py
│   └── load_processed_to_warehouse.py
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🔧 Features

### **1️⃣ Synthetic IoT Data Generator**

* Creates realistic equipment sensor readings:

  * temperature
  * vibration
  * pressure
  * operating hours
  * error codes
* Saves raw files to `data_lake/raw/yyyy/mm/dd/`

### **2️⃣ Data Transformation Pipeline**

`pipelines/transform_raw_to_processed.py`

* Cleans data
* Handles missing values
* Derives ML-ready features
* Exports processed CSVs

### **3️⃣ Data Warehouse Loader**

`pipelines/load_processed_to_warehouse.py`

* Creates fact tables
* Loads daily processed data
* Enforces unique constraints (avoids duplicates)

### **4️⃣ ML Training Pipeline**

`ml/train_failure_model.py`

* Trains RandomForest model
* Produces:

  * failure probability
  * risk categories
  * model artifact saved to `/models/`

### **5️⃣ Batch Scoring Pipeline**

`ml/batch_score_latest_readings.py`

* Applies ML model to latest sensor data
* Generates risk scores
* UPSERTs results into `ml_failure_risk_scores`

### **6️⃣ PostgreSQL + Adminer Dashboard**

* View fact tables & ML scores
* Inspect warehouse data
* Supports debugging + demos

---

# 🐳 Run Everything With Docker

### **Start database + Adminer UI**

```bash
docker-compose up -d
```

Adminer UI:
👉 [http://localhost:8080](http://localhost:8080)
Login:

* System: PostgreSQL
* Server: db
* User: postgres
* Password: postgres

---

# 💻 Run the Pipelines

### **Generate synthetic sensor readings**

```bash
python ingestion/generate_synthetic_data.py
```

### **Transform raw → processed**

```bash
python pipelines/transform_raw_to_processed.py
```

### **Load into PostgreSQL**

```bash
python pipelines/load_processed_to_warehouse.py
```

### **Train model**

```bash
python ml/train_failure_model.py
```

### **Score latest readings**

```bash
python ml/batch_score_latest_readings.py
```

---

# 📈 Exploratory Data Analysis (EDA)

Notebook located at:

```
notebooks/01_eda_and_baseline_model.ipynb
```

Includes:

* Data distribution plots
* Correlation heatmap
* Class imbalance review
* Baseline model performance
* Feature importance ranking

---

# 🧠 Machine Learning Model

**Model:** RandomForestClassifier
**Target:** `failed_within_24h` (binary classification)
**Outputs:**

* `risk_score` → probability of failure
* `risk_bucket` → LOW / MEDIUM / HIGH
* `source_model` → version tag

Model stored in:

```
models/failure_model_rf_v1.pkl
```

---

# 🛠 Tech Stack

| Layer           | Technology              |
| --------------- | ----------------------- |
| Language        | Python 3.10+            |
| Workflow        | Modular ETL scripts     |
| ML              | Scikit-learn            |
| Data Lake       | Local filesystem        |
| DB Warehouse    | PostgreSQL (Docker)     |
| Admin UI        | Adminer                 |
| Visualization   | Matplotlib, Seaborn     |
| Reproducibility | venv + requirements.txt |
| Orchestration   | CLI pipelines           |

---

# ▶️ How to Reproduce Locally

```bash
git clone https://github.com/Chenti-prog/equipment-failure-prediction.git
cd equipment-failure-prediction

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

docker-compose up -d
```

Then run any pipeline step using Python.

---

# ⭐ Future Improvements

* Add **Airflow DAG** orchestration
* Add **real-time streaming pipeline** (Kafka → Postgres)
* Add **Streamlit dashboard** for ML risk monitoring
* Add **unit tests + CI/CD**
* Build **REST inference API** with FastAPI
* Convert data lake to **Delta Lake** or **S3-style structure**
* Add **feature store** layer

---

# 🤝 Contributing

Pull requests are welcome.
Issues can be submitted for bugs or improvements.

---

# 📬 Contact

**Author:** Chentiwuni Yakubu
**GitHub:** [https://github.com/Chenti-prog](https://github.com/Chenti-prog)
**LinkedIn:** *(Add your link)*

---

If you'd like, I can also generate:

✔ Architecture diagram (SVG/PNG)
✔ Data flow diagram
✔ Example screenshots (Adminer, EDA plots)
✔ A version-tagging model registry structure

Just tell me!
