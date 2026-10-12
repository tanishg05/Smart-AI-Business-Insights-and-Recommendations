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

## Groq Intelligence

The copilot (⌘K / Ctrl+K), proactive insights, chart "Inspect" buttons and the Scenario Lab briefing are powered by Groq.

1. Create a key at https://console.groq.com/keys.
2. Add it to `backend/.env` (never commit this file):

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b
```

3. Restart the backend.

Without a key, every AI surface falls back to a built-in analytics engine that answers from the same computed metrics, so the dashboard stays fully usable. The key stays on the server and is never sent to the browser.

Before each Groq call the backend serialises a dense data brief (aggregate KPIs, top deficit SKU-locations, regional seasonality index, lead-time variance, turnover, forecast) into the system prompt.

## Views

- **Overview**: KPI badges (revenue, turnover, OTIF, stockout risk index, lead time) with deltas and sparklines, revenue trajectory vs moving-average baseline, proactive signals, top stock deficits
- **Demand & Sales**: region × channel stacked revenue, channel efficiency matrix, price elasticity scatter with fitted curve, category performance
- **Operations**: lead-time histogram with normal fit, lead time by region, stock vs velocity quadrant (Critical Low / Fast Mover / Overstocked / Dead Stock), replenishment queue
- **Seasonality**: season × region heatmap, 7-period Holt forecast with 95% band, seasonal volume and lead time
- **Scenario Lab**: live what-if sliders (supplier delay, demand surge, safety stock buffer, price) with lost sales, stockout probability, fill rate and holding cost
- **Intelligence Hub**: proactive insights, one-click prompts, recommendations

Region, channel, category and season filters apply to every view and to the copilot's context. Views are deep-linkable (`/#operations`) and switchable with keys 1–6.

## API Endpoints

- `GET /health`
- `GET /dashboard` (optional `region`, `channel`, `category`, `season`, `date_from`, `date_to`)
- `GET /api/datasets`, `POST /api/datasets/load`
- `GET /api/ai/status`
- `POST /api/ai/query` (SSE stream; `{query, context_filters?, conversation_history?, chart_context?, stream?}`)
- `GET /api/ai/proactive-insights`
- `POST /api/ai/scenario-simulate` (alias `/api/ai/scenario`)
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
