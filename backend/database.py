import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("market_intelligence.database")

# Detect database engine
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = DATABASE_URL and (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"))

# Normalize connection string for Postgres on Render/Neon if necessary
if IS_POSTGRES and DATABASE_URL.startswith("postgres://"):
    # psycopg2 requires "postgresql://" protocol header
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db_connection():
    """Establish connection to SQLite or PostgreSQL depending on DATABASE_URL."""
    if IS_POSTGRES:
        import psycopg2
        # Neon DB connection
        conn = psycopg2.connect(DATABASE_URL)
        # Create and isolate this project's tables in a custom schema "equisight"
        # so it doesn't conflict with other databases/projects in the same Neon project.
        cursor = conn.cursor()
        cursor.execute("CREATE SCHEMA IF NOT EXISTS equisight; SET search_path TO equisight;")
        conn.commit()
        cursor.close()
        return conn
    else:
        DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "market_intelligence.db"))
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def fetch_all_dict(cursor) -> List[Dict[str, Any]]:
    """Convert SQLite or Postgres cursor results into standard python dictionaries."""
    rows = cursor.fetchall()
    if not rows:
        return []
    
    if IS_POSTGRES:
        col_names = [desc[0] for desc in cursor.description]
        return [dict(zip(col_names, row)) for row in rows]
    else:
        return [dict(row) for row in rows]

def init_and_migrate_db():
    """Initializes tables and performs migrations if columns are missing for SQLite or Postgres."""
    logger.info(f"Connecting to database (Engine: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}) for initialization...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create watchlist table
    if IS_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(50) UNIQUE NOT NULL,
                added_date VARCHAR(100) NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                added_date TEXT NOT NULL
            )
        """)
    
    # Seed default watchlist if empty
    cursor.execute("SELECT COUNT(*) FROM watchlist")
    count_row = cursor.fetchone()
    count = count_row[0] if count_row else 0
    if count == 0:
        logger.info("Seeding default watchlist...")
        defaults = ["RECLTD.NS", "JINDALDRILL.NS", "TCS.NS", "RELIANCE.NS"]
        now = datetime.now(timezone.utc).isoformat()
        
        if IS_POSTGRES:
            cursor.executemany(
                "INSERT INTO watchlist (ticker, added_date) VALUES (%s, %s) ON CONFLICT (ticker) DO NOTHING",
                [(t, now) for t in defaults]
            )
        else:
            cursor.executemany(
                "INSERT OR IGNORE INTO watchlist (ticker, added_date) VALUES (?, ?)",
                [(t, now) for t in defaults]
            )
    
    # 2. Create asset_analysis table
    if IS_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_analysis (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(50) NOT NULL,
                date VARCHAR(100) NOT NULL,
                growth_score INTEGER NOT NULL,
                sentiment VARCHAR(50) NOT NULL,
                raw_analysis TEXT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                growth_score INTEGER NOT NULL,
                sentiment TEXT NOT NULL,
                raw_analysis TEXT NOT NULL
            )
        """)
    
    # 3. Migrate: Add new columns if missing
    if IS_POSTGRES:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'asset_analysis' AND table_schema = 'equisight'")
        columns = [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute("PRAGMA table_info(asset_analysis)")
        columns = [row["name"] for row in cursor.fetchall()]
    
    new_cols = {
        "forward_pe": "REAL",
        "revenue_growth": "REAL",
        "debt_to_equity": "REAL",
        "headlines": "TEXT",
        "key_insight": "TEXT"
    }
    
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            logger.info(f"Migration: Adding column '{col_name}' ({col_type}) to 'asset_analysis'")
            try:
                cursor.execute(f"ALTER TABLE asset_analysis ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                logger.error(f"Failed to add column {col_name}: {e}")
                
    conn.commit()
    conn.close()
    logger.info("Database initialization and migrations finished successfully.")

# CRUD Watchlist
def get_watchlist() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM watchlist ORDER BY id ASC")
    rows = fetch_all_dict(cursor)
    tickers = [row["ticker"] for row in rows]
    conn.close()
    return tickers

def add_to_watchlist(ticker: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = "%s" if IS_POSTGRES else "?"
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            f"INSERT INTO watchlist (ticker, added_date) VALUES ({placeholder}, {placeholder})", 
            (ticker.upper().strip(), now)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to add ticker {ticker}: {e}")
        return False
    finally:
        conn.close()

def delete_from_watchlist(ticker: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = "%s" if IS_POSTGRES else "?"
    try:
        cursor.execute(f"DELETE FROM watchlist WHERE ticker = {placeholder}", (ticker.upper().strip(),))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        logger.error(f"Error deleting ticker {ticker}: {e}")
        return False
    finally:
        conn.close()

# CRUD Analysis
def store_analysis_record(ticker: str, data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
    """Store complete analysis result in SQLite or Postgres database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = "%s" if IS_POSTGRES else "?"
    try:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        import json
        
        headlines_str = json.dumps(data.get("news_headlines", []))
        
        query = f"""
            INSERT INTO asset_analysis (
                ticker, date, growth_score, sentiment, 
                forward_pe, revenue_growth, debt_to_equity, headlines,
                key_insight, raw_analysis
            ) VALUES ({','.join([placeholder]*10)})
        """
        
        cursor.execute(query, (
            ticker,
            current_date,
            analysis["growth_score"],
            analysis["sentiment"],
            data.get("forward_pe"),
            data.get("revenue_growth"),
            data.get("debt_to_equity"),
            headlines_str,
            analysis["key_insight"],
            json.dumps(analysis)
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error storing analysis record for {ticker}: {e}", exc_info=True)
        return False
    finally:
        conn.close()

def get_latest_analyses() -> List[Dict[str, Any]]:
    """Retrieve the single latest analysis for each ticker in the watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.* FROM asset_analysis a
        INNER JOIN (
            SELECT ticker, MAX(date) as max_date 
            FROM asset_analysis 
            GROUP BY ticker
        ) b ON a.ticker = b.ticker AND a.date = b.max_date
        ORDER BY a.ticker ASC
    """)
    rows = fetch_all_dict(cursor)
    conn.close()
    
    import json
    results = []
    for r in rows:
        headlines = []
        if r.get("headlines"):
            try:
                headlines = json.loads(r["headlines"])
            except Exception:
                headlines = [h.strip() for h in r["headlines"].split("\n") if h.strip()]
        
        results.append({
            "id": r["id"],
            "ticker": r["ticker"],
            "date": r["date"],
            "growth_score": r["growth_score"],
            "sentiment": r["sentiment"],
            "forward_pe": r["forward_pe"],
            "revenue_growth": r["revenue_growth"],
            "debt_to_equity": r["debt_to_equity"],
            "headlines": headlines,
            "key_insight": r.get("key_insight"),
            "raw_analysis": r["raw_analysis"]
        })
    return results

def get_ticker_history(ticker: str) -> List[Dict[str, Any]]:
    """Retrieve historical analysis records for a given ticker to plot trends."""
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = "%s" if IS_POSTGRES else "?"
    cursor.execute(f"""
        SELECT date, growth_score, sentiment 
        FROM asset_analysis 
        WHERE ticker = {placeholder} 
        ORDER BY date ASC
    """, (ticker.upper().strip(),))
    rows = fetch_all_dict(cursor)
    conn.close()
    
    return [{"date": r["date"], "growth_score": r["growth_score"], "sentiment": r["sentiment"]} for r in rows]
