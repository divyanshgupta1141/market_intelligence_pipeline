import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import WatchlistManager from './components/WatchlistManager';
import PipelineControl from './components/PipelineControl';
import { API_BASE_URL } from './config';

export default function App() {
  const [watchlist, setWatchlist] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch watched tickers
  const fetchWatchlist = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlist`);
      if (!response.ok) throw new Error("Failed to fetch watchlist");
      const data = await response.json();
      setWatchlist(data);
    } catch (err) {
      console.error("Error loading watchlist:", err);
    }
  };

  // Fetch latest SQLite analyses records
  const fetchAnalyses = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/analysis/latest`);
      if (!response.ok) throw new Error("Failed to fetch analyses");
      const data = await response.json();
      setAnalyses(data);
    } catch (err) {
      console.error("Error loading analyses:", err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchWatchlist();
    fetchAnalyses();
  }, []);

  const handleWatchlistChanged = () => {
    fetchWatchlist();
    // Watchlist change could mean deleted tickers or newly added ones, refresh dashboard state
    fetchAnalyses();
  };

  const handlePipelineCompleted = () => {
    // Refresh the dashboard cards since new analyses records are stored in SQLite
    fetchAnalyses();
  };

  return (
    <div className="app-wrapper">
      {/* Header section */}
      <header className="app-header">
        <div className="header-title-section">
          <h1>EquiSight</h1>
          <p>
            <span className="pulse-badge"></span>
            Autonomous Market Intelligence Agent Ingestion Active
          </p>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'right' }}>
          <div>Engine Version: v1.1.0</div>
          <div>Target: Indian Equities (NSE)</div>
        </div>
      </header>

      {/* Watchlist & Action Controls Row */}
      <div className="top-controls-grid">
        <WatchlistManager 
          watchlist={watchlist} 
          onWatchlistChanged={handleWatchlistChanged} 
        />
        <PipelineControl 
          watchlist={watchlist} 
          onRunCompleted={handlePipelineCompleted} 
        />
      </div>

      {/* Main dashboard data visualization */}
      <main style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.6rem', letterSpacing: '-0.02em' }}>
          Market Intelligence Dashboard
        </h2>
        <Dashboard 
          analyses={analyses} 
          loading={loading} 
        />
      </main>
    </div>
  );
}
