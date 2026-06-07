# EquiSight: Autonomous Market Intelligence Dashboard

[![Live Deployment](https://img.shields.io/badge/Live_Demo-Render-46E3B7?style=for-the-badge&logo=render)](https://equisight-dashboard.onrender.com/)

EquiSight is a production-ready, full-stack market intelligence platform. It dynamically ingests equity data from Yahoo Finance, executes AI-driven fundamental and sentiment analysis via a Gemini LLM reasoning layer, and surfaces structured financial intelligence through a high-performance, glassmorphic React dashboard.

---

## 📂 Architecture & Folder Structure

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

## 🚀 Getting Started

### 1. Setup Backend (Python FastAPI)

The backend runs on Python 3.10+ and utilizes SQLite for lightweight, zero-config state management.

Navigate to the project root directory and activate your virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate

```

Install the backend dependencies:

```bash
pip install -r backend/requirements.txt

```

Configure your environment variables by creating a `.env` file in the `backend/` directory:

```bash
echo 'GEMINI_API_KEY="your-gemini-api-key"' > backend/.env

```

*(Note: If no API key is provided, EquiSight gracefully degrades into a Zero-Cost Local Development Mode, generating deterministic financial mocks so you can evaluate the platform's UI/UX without consuming tokens.)*

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload --port 8000

```

*You can access the interactive Swagger API documentation directly at `http://localhost:8000/docs`.*

### 2. Setup Frontend (Vite + React)

The frontend is a single-page web dashboard optimized with high-performance Vanilla CSS (dark-theme glassmorphism and micro-animations).

Open a new terminal window, navigate to the frontend directory, and install the Node packages:

```bash
cd frontend
npm install

```

Boot up the Vite development server:

```bash
npm run dev

```

*The dashboard will automatically launch in your browser, typically at `http://localhost:5173`.*

