import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

export default function WatchlistManager({ watchlist, onWatchlistChanged }) {
  const [newTicker, setNewTicker] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleAddTicker = async (e) => {
    e.preventDefault();
    const symbol = newTicker.toUpperCase().trim();
    if (!symbol) return;
    
    setError('');
    setSubmitting(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: symbol })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add ticker");
      }
      
      setNewTicker('');
      onWatchlistChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTicker = async (symbol) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/watchlist/${symbol}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error("Failed to delete ticker");
      onWatchlistChanged();
    } catch (err) {
      console.error("Error deleting ticker", symbol, err);
    }
  };

  return (
    <div className="glass-panel">
      <div className="panel-title">
        <span>📋</span> Watchlist Monitor
      </div>
      
      <form onSubmit={handleAddTicker} className="input-group">
        <input
          type="text"
          className="custom-input"
          placeholder="Enter Ticker Symbol (e.g. TCS.NS)"
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          disabled={submitting}
        />
        <button type="submit" className="btn btn-primary" disabled={submitting || !newTicker.trim()}>
          {submitting ? 'Adding...' : 'Add'}
        </button>
      </form>

      {error && <div style={{ color: 'var(--bearish)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>}

      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Currently Tracking:</div>
      
      <div className="watchlist-items-list">
        {watchlist.length === 0 ? (
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>No tickers in watchlist.</span>
        ) : (
          watchlist.map((ticker) => (
            <span key={ticker} className="watchlist-pill">
              {ticker}
              <button
                type="button"
                className="btn-icon-only btn-danger-hover"
                style={{ padding: '2px', fontSize: '0.75rem', color: 'var(--text-muted)' }}
                onClick={() => handleDeleteTicker(ticker)}
                title={`Remove ${ticker}`}
              >
                ✕
              </button>
            </span>
          ))
        )}
      </div>
    </div>
  );
}
