# EquiSight: Autonomous Market Intelligence Dashboard

EquiSight is a project-level, production-ready, full-stack application that ingests equity data from Yahoo Finance, performs AI-powered fundamental and sentiment analysis (using Gemini LLM reasoning layer), and visualizes the structured intelligence in a premium glassmorphic dashboard.

## Folder Structure

```text
market_intelligence_pipeline/
├── backend/
│   ├── main.py            # FastAPI Web Server
│   ├── database.py        # Database operations & CRUD (SQLite)
│   ├── pipeline.py        # Ingestion layer & Gemini LLM reasoning
│   └── requirements.txt   # Python dependencies (FastAPI, uvicorn, etc.)
├── frontend/
│   ├── package.json       # Node.js configurations
│   ├── index.html         # Root HTML
│   └── src/
│       ├── main.jsx       # React entry point
│       ├── App.jsx        # App core structure & state
│       ├── index.css      # Custom design system & animations (Vanilla CSS)
│       └── components/
│           ├── Dashboard.jsx        # Cards grid & detail inspect modal
│           ├── TickerCard.jsx       # Info visualization & historical sparkline
│           ├── WatchlistManager.jsx # CRUD pills & watchlist adding
│           └── PipelineControl.jsx  # Logs viewer & execution trigger
└── README.md
```

---

## Getting Started

### 1. Setup Backend (Python FastAPI)

The backend runs on Python 3.10+ and uses SQLite.

1. Navigate to the project root directory and activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Upgrade/install dependencies using the backend's `requirements.txt`:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start the FastAPI server on port 8000:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"   # Optional: falls back to local mocks if not provided
   uvicorn backend.main:app --reload --port 8000
   ```
   *Note: If no API key is specified, EquiSight runs in a robust mock offline mode generating realistic financial calculations locally so you can test all operations for free!*

4. You can access the API Swagger docs directly at `http://localhost:8000/docs`.

### 2. Setup Frontend (Vite + React)

The frontend is a single-page web dashboard styled with high-performance Vanilla CSS (dark-theme glassmorphism and micro-animations).

1. Open a new terminal window, navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install npm packages (if you haven't already):
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the local URL (usually `http://localhost:5173`).

---

## Key Features

1. **Dashboard Overview Grid**: View the latest growth scores, sentiment status, and key financial ratios (P/E, YoY Growth, Debt/Equity) at a glance.
2. **Watchlist Monitor**: Live add and remove tickers (e.g. `TCS.NS`, `RELIANCE.NS`, `INFY.NS`). The backend queries Yahoo Finance data dynamically.
3. **Execution Console**: Click "Trigger Watchlist Analysis" to run the background agent pipeline. A live scrollable terminal in the UI displays real-time execution logs from the server.
4. **SVG Historical Sparkline**: Every stock card plots a custom SVG trend line representing the ticker's historical growth scores across multiple runs, letting you monitor trends over time.
5. **Detailed Insight Inspection**: Click on any stock card to open an interactive modal with full metrics, Yahoo Finance news headlines, and the detailed generative analysis summary.
