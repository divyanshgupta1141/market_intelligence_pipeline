import os
import logging
import collections
import threading
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Import local modules
from backend.database import (
    init_and_migrate_db,
    get_watchlist,
    add_to_watchlist,
    delete_from_watchlist,
    get_latest_analyses,
    get_ticker_history
)
from backend.pipeline import run_pipeline_for_watchlist

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market_intelligence")

# Custom log collector for the frontend
class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity=100):
        super().__init__()
        self.logs = collections.deque(maxlen=capacity)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append(msg)
        except Exception:
            self.handleError(record)

    def get_all(self):
        return list(self.logs)

    def clear(self):
        self.logs.clear()

memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
# Add memory handler to root logger to capture all application and pipeline logs
logging.getLogger().addHandler(memory_handler)

app = FastAPI(title="Autonomous Market Intelligence API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App State
pipeline_running = False
pipeline_lock = threading.Lock()

# Initial database migration on startup
@app.on_event("startup")
def startup_event():
    init_and_migrate_db()
    logger.info("FastAPI Application Startup Complete.")

# Models
class TickerRequest(BaseModel):
    ticker: str

class PipelineRunRequest(BaseModel):
    tickers: Optional[List[str]] = None

# Endpoints
@app.get("/api/watchlist", response_model=List[str])
def read_watchlist():
    return get_watchlist()

@app.post("/api/watchlist")
def create_watchlist_item(req: TickerRequest):
    ticker = req.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty.")
    success = add_to_watchlist(ticker)
    if not success:
        raise HTTPException(status_code=400, detail="Ticker already exists in watchlist.")
    return {"message": f"Ticker {ticker} added successfully."}

@app.delete("/api/watchlist/{ticker}")
def delete_watchlist_item(ticker: str):
    ticker = ticker.upper().strip()
    success = delete_from_watchlist(ticker)
    if not success:
        raise HTTPException(status_code=404, detail="Ticker not found in watchlist.")
    return {"message": f"Ticker {ticker} deleted successfully."}

@app.get("/api/analysis/latest")
def read_latest_analysis():
    return get_latest_analyses()

@app.get("/api/analysis/history/{ticker}")
def read_ticker_history(ticker: str):
    return get_ticker_history(ticker)

@app.get("/api/pipeline/logs")
def read_pipeline_logs():
    """Retrieve in-memory logs for pipeline executions."""
    return {"logs": memory_handler.get_all(), "running": pipeline_running}

def execute_pipeline_task(tickers_to_run: List[str]):
    global pipeline_running
    try:
        logger.info(f"Background task: Running pipeline for: {tickers_to_run}")
        run_pipeline_for_watchlist(tickers_to_run)
    except Exception as e:
        logger.error(f"Error in background pipeline run: {e}", exc_info=True)
    finally:
        with pipeline_lock:
            pipeline_running = False
        logger.info("Background pipeline task execution finished.")

@app.post("/api/pipeline/run")
def trigger_pipeline_run(req: PipelineRunRequest, background_tasks: BackgroundTasks):
    global pipeline_running
    
    with pipeline_lock:
        if pipeline_running:
            raise HTTPException(status_code=409, detail="Pipeline run is already in progress.")
        pipeline_running = True

    # Identify tickers to execute
    if req.tickers and len(req.tickers) > 0:
        tickers = [t.upper().strip() for t in req.tickers]
    else:
        tickers = get_watchlist()

    if not tickers:
        pipeline_running = False
        raise HTTPException(status_code=400, detail="Watchlist is empty. Cannot run pipeline.")

    # Clear prior logs to start a fresh log view in the frontend
    memory_handler.clear()
    logger.info("Starting pipeline run requested via Web UI...")
    
    # Run in background
    background_tasks.add_task(execute_pipeline_task, tickers)
    
    return {"message": "Pipeline run started.", "tickers": tickers}
