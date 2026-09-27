# Cyber Crime Forecast

**I4C Command Center — Predictive Cybercrime Intelligence and Response Dashboard**

A cybercrime intelligence and response dashboard for suspicious financial activity, ATM risk zones, and account tracing.

## 1. Overview

This project supports cybercrime investigation teams by combining complaint data, transaction flow analysis, and ATM cashout patterns into a single operational dashboard.

It helps identify suspicious account activity, trace likely money movement, and identify high-risk ATM locations associated with mule networks.

The system is intended for cybercrime units, police command centres, and authorized investigation staff. It is built around Indian cybercrime reporting data and transaction simulation patterns, with a map-based interface for local operational review.

## 2. Problem, Solution, and Target Users

### Problem

Cybercrime investigations often involve fragmented data across complaints, money trails, and physical cashout points. Investigators need to connect victim complaints to suspicious financial flows and identify where funds are likely being withdrawn.

### Solution

The application brings together:

* NCRP complaint records
* Mule transaction flow analysis
* ATM cashout risk scoring
* Map-based hotspot detection
* Nearby police and bank discovery
* Investigation workflows for suspicious accounts and case tracing

### Target Users

* Police cyber cells
* Law enforcement command centres
* Authorized officers working in cybercrime investigation workflows

## 3. Key Features

The following features are implemented in the current codebase:

* Government-style login portal for authorized officers
* FastAPI backend with CORS enabled for local frontend access
* Live map overview with complaint heatmap and risk-based hotspot visualization
* Risk scoring for suspicious ATM and cashout zones
* Case tracing from NCRP complaint numbers to likely ATM areas
* Forward account tracing and transaction trail analysis
* Fan-out detection for suspicious account activity patterns
* Graph-based mule network exploration using account relationships
* CSV fallback support when PostgreSQL is unavailable
* Real-time nearby place lookup using OpenStreetMap Overpass/Nominatim

## 4. Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* psycopg2
* Pandas
* NumPy
* NetworkX
* scikit-learn
* SciPy
* python-dotenv

### Frontend

* React
* TypeScript
* Vite
* Leaflet
* react-leaflet
* Axios
* Lucide React

### Database

* PostgreSQL
* Optional PostGIS extension
* CSV fallback data files for local/offline operation

## 5. Architecture

The project follows a three-layer architecture:

1. **Frontend** — React dashboard and map interface
2. **Backend** — FastAPI investigation and analytics APIs
3. **Data Layer** — PostgreSQL or CSV-backed complaints, transactions, and ATM records

### Runtime Flow

* The frontend calls the FastAPI API for authentication, dashboard analytics, case tracing, and account tracking.
* The backend loads complaint and transaction data from PostgreSQL when configured, or falls back to CSV files.
* The ML/risk engine builds a transaction graph, evaluates spatial-temporal risk signals, and predicts suspicious ATM hotspots.
* The map service resolves nearby police stations and banks using OpenStreetMap sources.

## 6. Project Structure

```text
Cyber-Crime-Forecast-main/
├── .env
├── .gitignore
├── example.env
├── requirements.txt
├── data/
│   ├── atm_cashouts.csv
│   ├── cfcfrms_transactions.csv
│   ├── ncrp_complaints.csv
│   └── export.json
├── backend/
│   ├── AccountTracking/
│   │   └── AccountTracking.py
│   ├── Map/
│   │   └── MapComponent.py
│   ├── api/
│   │   ├── app.py
│   │   └── auth.py
│   ├── data_generation/
│   │   └── generate_data.py
│   └── ml/
│       └── ml_engine.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   ├── public/
│   └── index.html
├── scripts/
│   ├── import_india_atms.py
│   ├── migrate_to_postgres.py
│   ├── reset_db_postgis.py
│   └── set_loc_complaint.py
└── README.md
```

## 7. AI/ML Components

The project includes a graph- and risk-based analytics engine implemented in:

```text
backend/ml/ml_engine.py
```

### Implemented Analytical Logic

* Directed transaction graph construction using NetworkX
* Mule-chain tracing through graph traversal
* Hotspot prediction using Kernel Density Estimate (KDE)
* Hawkes-inspired temporal and spatial excitation logic
* Network-link scoring for terminal nodes related to suspicious accounts
* Risk normalization from 0 to 1 for hotspot ranking

### Important Note

The system uses a **rule-based and heuristic risk model** based on transaction patterns and spatial signals. It is not presented as a production-grade model trained for safety-critical decision-making.

## 8. Database

The application is designed to work with PostgreSQL.

### Main Tables

* `ncrp_complaints`
* `cfcfrms_transactions`
* `atm_cashouts`

### Optional Tables

* `police_stations`
* `users`
* `atm_locations`

When PostgreSQL is unavailable or incorrectly configured, the application falls back to CSV files under the `data/` directory.

## 9. User Roles

The implemented authentication supports:

* `admin`
* `officer`

The login system returns user metadata including:

* Username
* Role
* Optional officer ID

The database reset script seeds users with credentials and associated police station IDs for local testing.

## 10. Installation

### Prerequisites

* Python 3.10+
* Node.js 18+
* PostgreSQL with optional PostGIS

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Cyber-Crime-Forecast-main
```

### 2. Create Python Virtual Environment

```bash
python -m venv .venv
```

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## 11. Environment Variables

Create or update the root `.env` file based on `example.env`.

### Required

```env
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database_name>
```

### Frontend

```env
VITE_API_URL=http://localhost:8000
```

### Optional / Legacy Values

```env
VITE_GOOGLE_MAPS_API_KEY=<your-key>
VITE_GOOGLE_MAPS_MAP_ID=<your-map-id>
```

These values are placeholders. Real credentials must never be committed to the repository.

## 12. Database Setup

### Option A: PostgreSQL Import Using CSVs

From the project root:

```bash
python scripts/migrate_to_postgres.py
```

This creates the main tables and imports data from the CSV files in `data/`.

### Option B: PostgreSQL + PostGIS Reset

```bash
python scripts/reset_db_postgis.py
```

This enables PostGIS, recreates the schema, seeds users and police stations, and imports the dataset.

### Generate Synthetic Data

```bash
python backend/data_generation/generate_data.py
```

## 13. Run Instructions

### Start Backend

From the project root:

```bash
uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8000
```

Alternative:

```bash
python -m uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8000
```

### Start Frontend

From the `frontend` directory:

```bash
npm run dev
```

The Vite application is usually available at:

```text
http://localhost:5173
```

## 14. API Endpoints

### Authentication

| Method | Endpoint             | Purpose                                         |
| ------ | -------------------- | ----------------------------------------------- |
| POST   | `/api/v1/auth/login` | Authenticate user and return role/user metadata |

### Analytics and Prediction

| Method | Endpoint                         | Purpose                                                      |
| ------ | -------------------------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/predict/complaint`      | Trace complaint and return mule chain and predicted hotspots |
| GET    | `/api/v1/analytics/risk-heatmap` | Return GeoJSON risk map data                                 |
| GET    | `/api/v1/alerts/active`          | Return active high-risk alerts                               |
| GET    | `/api/v1/analytics/stats`        | Return dashboard statistics                                  |

### Map Services

| Method | Endpoint                       |
| ------ | ------------------------------ |
| GET    | `/api/map/overview`            |
| GET    | `/api/map/heatmap`             |
| GET    | `/api/map/hotspots`            |
| GET    | `/api/map/risk-zones`          |
| GET    | `/api/map/statistics`          |
| GET    | `/api/map/trace-case/{ack_no}` |

### Account Tracking

| Method | Endpoint                                              |
| ------ | ----------------------------------------------------- |
| GET    | `/api/account-tracking/`                              |
| GET    | `/api/account-tracking/transaction/{transaction_id}`  |
| GET    | `/api/account-tracking/fan-out/{account_number}`      |
| GET    | `/api/account-tracking/fan-out/tree/{account_number}` |
| GET    | `/api/account-tracking/{account_number}`              |

## 15. Usage

1. Start PostgreSQL and configure `.env`.
2. Run the database setup script.
3. Start the FastAPI backend.
4. Start the Vite frontend.
5. Sign in with a valid seeded user.
6. Use the dashboard to:

   * Search by NCRP ACK number
   * View suspicious hotspot risk overlays
   * Inspect account money trails
   * Review fan-out activity and account flows
   * Trace complaints to likely ATM areas and nearby services

## 16. Security

### Implemented Security

* Password verification using SHA-256 hashes
* Authorized login flow in the UI
* CORS configuration for local development
* Sensitive configuration stored through `.env`

### Current Security Limitations

* No JWT, OAuth, or external identity provider
* No token rotation
* No session-expiry enforcement
* No MFA
* Local storage is used for frontend authentication state
* Database credentials and API keys must be kept out of version control

## 17. Screenshots

Screenshots are not included in the repository.

## 18. Limitations

* The system relies on synthetic or sample datasets unless production data is imported.
* Map and alerting logic is heuristic and explanatory, not a validated operational model.
* No production-grade ETL pipeline is implemented.
* Authentication uses a simple credential store.
* Enterprise security features are not implemented.
* Local development CORS settings are used.
* The system is not configured for production deployment.

## 19. Future Enhancements

The following are planned extensions and are **not part of the current implementation**:

* JWT-based authentication and safer session handling
* Stronger role-based authorization
* Real-time streaming alerts and notifications
* Advanced ML training on historical fraud patterns
* Secure staging and production deployment
* Exportable investigation reports
* Expanded geospatial analytics
* District-level intelligence reporting

## 20. License

Not specified. No `LICENSE` file was found in the repository.

---

## Project Summary

**Cyber Crime Forecast** is a cybercrime investigation dashboard that combines suspicious financial-flow analysis, mule-account tracing, transaction graphs, ATM hotspot risk analysis, and map-based intelligence to support authorized cybercrime investigation workflows.
