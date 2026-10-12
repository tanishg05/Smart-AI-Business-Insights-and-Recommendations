<<<<<<< HEAD
# Smart-AI-Business-Insights-and-Recommendations
=======
# Supply Chain Intelligence Dashboard

A full-stack analytics dashboard for supply chain monitoring, sales analysis, seasonal demand tracking, operational insights, and AI-style recommendation generation.

## Overview

This project enables users to upload a CSV dataset and instantly explore:
- executive KPI summaries
- sales trend analysis
- regional and channel performance
- seasonal demand patterns
- operational efficiency metrics
- AI-driven demand classification and recommendations

## Features

- Upload a CSV dataset from the frontend
- View KPI cards and overview analytics
- Explore sales performance by region, channel, and category
- Analyze seasonality and regional demand heatmaps
- Review delivery and stock utilization metrics
- Identify high-demand segments and recommended actions

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI
- Data processing: Pandas + NumPy
- API communication: Axios
- Styling: CSS and component-based React UI

## Architecture

```text
Frontend
   ↓
FastAPI backend
   ↓
Analytics/data-processing service
   ↓
CSV dataset upload and dashboard payload generation
```

## Project Structure

```text
project-root/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── analytics.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── data_service.py
│   ├── uploads/
│   │   ├── test.csv
│   │   └── test_supply_chain.csv
│   └── utils/
│       ├── __init__.py
│       └── logging.py
├── frontend/
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.css
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       └── utils/
├── docs/
│   └── research/
│       └── DET.ipynb
├── .gitignore
├── .env.example
├── README.md
└── ...
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## Installation

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Environment Variables

Use the example files as templates:
- `backend/.env.example`
- `frontend/.env.example`
- root `.env.example`

Example values:

```env
# frontend/.env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

```env
# backend/.env
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

Do not commit real secret or local environment files. Keep only `.env.example` files in the repository.

## Running Locally

### Terminal 1 — Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

## Local URLs

- Frontend: http://localhost:3000
- Backend: http://127.0.0.1:8000

## API Endpoints

- `GET /health`
- `GET /dashboard`
- `GET /sales`
- `GET /seasonality`
- `GET /operations`
- `GET /insights`
- `GET /recommendations`
- `POST /upload`

## Deployment

This project is structured for a standard full-stack deployment:
- frontend deployed as a static app or Node host
- backend deployed as a FastAPI service
- uploaded CSV files processed server-side

Before production deployment:
- set the frontend API base URL via `VITE_API_BASE_URL`
- configure allowed CORS origins for the backend
- keep uploaded files in a proper production storage location when needed

## Future Development

Future work should generally happen in:
- `frontend/src/` for dashboard UI and logic
- `backend/routes/` and `backend/services/` for API behavior and analytics processing

## License

No license file was found in the project, so no explicit license is declared.
>>>>>>> a70a14d (Baseline: existing supply chain dashboard)
