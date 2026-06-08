#!/usr/bin/env python3
"""
Unit tests for Autonomous Market Intelligence Pipeline.
Run with: python -m unittest test_pipeline.py
"""

import unittest
import json
import sqlite3
import os
from pipeline import parse_json_safely, init_db, store_analysis, generate_mock_analysis


class TestMarketIntelligencePipeline(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_market_intelligence.db"

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_parse_json_safely_valid(self):
        # Test clean JSON parsing
        raw_json = '{"growth_score": 85, "sentiment": "Bullish", "key_insight": "Strong earnings growth."}'
        result = parse_json_safely(raw_json)
        self.assertIsNotNone(result)
        self.assertEqual(result["growth_score"], 85)
        self.assertEqual(result["sentiment"], "Bullish")
        self.assertEqual(result["key_insight"], "Strong earnings growth.")

    def test_parse_json_safely_markdown(self):
        # Test JSON with markdown formatting
        raw_json_md = '```json\n{"growth_score": 40, "sentiment": "Bearish", "key_insight": "High debt load."}\n```'
        result = parse_json_safely(raw_json_md)
        self.assertIsNotNone(result)
        self.assertEqual(result["growth_score"], 40)
        self.assertEqual(result["sentiment"], "Bearish")

    def test_parse_json_safely_regex_fallback(self):
        # Test JSON embedded in other text
        raw_text = 'Here is the result: {"growth_score": 50, "sentiment": "Neutral", "key_insight": "Fairly valued."} hope this helps.'
        result = parse_json_safely(raw_text)
        self.assertIsNotNone(result)
        self.assertEqual(result["growth_score"], 50)
        self.assertEqual(result["sentiment"], "Neutral")

    def test_parse_json_safely_invalid(self):
        # Test invalid JSON
        raw_invalid = '{"growth_score": "not_an_int", "sentiment": "Bullish"}'
        result = parse_json_safely(raw_invalid)
        self.assertIsNone(result)

    def test_database_operations(self):
        # Initialize test DB
        conn = init_db(self.test_db)
        self.assertIsInstance(conn, sqlite3.Connection)

        # Create dummy analysis
        ticker = "TEST.NS"
        analysis = {
            "growth_score": 75,
            "sentiment": "Bullish",
            "key_insight": "Test insight."
        }

        # Store analysis
        stored = store_analysis(conn, ticker, analysis)
        self.assertTrue(stored)

        # Retrieve and verify
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, growth_score, sentiment, raw_analysis FROM asset_analysis WHERE ticker=?", (ticker,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "TEST.NS")
        self.assertEqual(row[1], 75)
        self.assertEqual(row[2], "Bullish")
        
        # Verify stored raw_analysis JSON matches original dict
        stored_analysis = json.loads(row[3])
        self.assertEqual(stored_analysis["key_insight"], "Test insight.")

        conn.close()

    def test_generate_mock_analysis(self):
        # Verify the helper generates correct types
        ticker_data = {
            "ticker": "TEST.NS",
            "forward_pe": 15,
            "revenue_growth": 0.25,
            "debt_to_equity": 20.0
        }
        mock_result = generate_mock_analysis(ticker_data)
        self.assertIn("growth_score", mock_result)
        self.assertIn("sentiment", mock_result)
        self.assertIn("key_insight", mock_result)
        self.assertTrue(1 <= mock_result["growth_score"] <= 100)
        self.assertIn(mock_result["sentiment"], ["Bullish", "Bearish", "Neutral"])

    def test_fetch_financial_data_yfinance_rate_limit_fallback(self):
        # Setup cache database record
        db_path = "test_market_intelligence.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                growth_score INTEGER NOT NULL,
                sentiment TEXT NOT NULL,
                forward_pe REAL,
                revenue_growth REAL,
                debt_to_equity REAL,
                headlines TEXT,
                raw_analysis TEXT NOT NULL
            )
        """)
        # Seed cache for TEST_STOCK.NS
        cursor.execute("""
            INSERT INTO asset_analysis (ticker, date, growth_score, sentiment, forward_pe, revenue_growth, debt_to_equity, headlines, raw_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "TEST_STOCK.NS", "2026-06-08 12:00:00", 80, "Bullish", 12.5, 0.18, 45.0, 
            '["Test headline 1", "Test headline 2"]', '{"growth_score": 80}'
        ))
        conn.commit()
        conn.close()
        
        # Modify pipeline.DB_FILE to point to our test db path temporarily
        import pipeline
        original_db = pipeline.DB_FILE
        pipeline.DB_FILE = db_path
        
        try:
            import unittest.mock as mock
            with mock.patch("yfinance.Ticker") as mock_ticker:
                mock_ticker.side_effect = Exception("Rate limited mock exception")
                
                # Fetch financial data
                result = pipeline.fetch_financial_data("TEST_STOCK.NS")
                
                self.assertIsNotNone(result)
                self.assertEqual(result["ticker"], "TEST_STOCK.NS")
                self.assertEqual(result["forward_pe"], 12.5)
                self.assertEqual(result["revenue_growth"], 0.18)
                self.assertEqual(result["debt_to_equity"], 45.0)
                self.assertEqual(result["news_headlines"], ["Test headline 1", "Test headline 2"])
        finally:
            pipeline.DB_FILE = original_db
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
