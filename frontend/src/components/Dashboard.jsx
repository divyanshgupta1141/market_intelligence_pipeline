import React, { useState } from 'react';
import TickerCard from './TickerCard';

export default function Dashboard({ analyses, loading }) {
  const [selectedStock, setSelectedStock] = useState(null);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spin empty-state-icon">🌀</div>
        <h2>Loading Market Intelligence...</h2>
        <p>Connecting to SQLite database and retrieving stock analysis data.</p>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🔮</div>
        <h2>No Analysis Available</h2>
        <p>Add stocks to the watchlist and trigger the market intelligence pipeline to see results here.</p>
      </div>
    );
  }

  const formatPE = (val) => val != null ? val.toFixed(2) : 'N/A';
  const formatGrowth = (val) => val != null ? `${(val * 100).toFixed(1)}%` : 'N/A';
  const formatDebt = (val) => val != null ? `${val.toFixed(1)}%` : 'N/A';

  return (
    <div>
      <div className="dashboard-grid">
        {analyses.map(stock => (
          <TickerCard 
            key={stock.id} 
            analysis={stock} 
            onClick={setSelectedStock} 
          />
        ))}
      </div>

      {/* Details Modal */}
      {selectedStock && (
        <div className="modal-overlay" onClick={() => setSelectedStock(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 className="card-ticker-name" style={{ fontSize: '2rem' }}>{selectedStock.ticker}</h2>
                <p className="card-date" style={{ fontSize: '0.9rem' }}>Analysis generated on: {selectedStock.date}</p>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <span className={`sentiment-badge ${selectedStock.sentiment.toLowerCase()}`} style={{ fontSize: '0.9rem', padding: '0.4rem 0.8rem' }}>
                  {selectedStock.sentiment}
                </span>
                <button className="btn-icon-only" onClick={() => setSelectedStock(null)} style={{ fontSize: '1.25rem' }}>✕</button>
              </div>
            </div>

            <div className="modal-body">
              {/* Score & Key Metrics Panel */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.2)' }}>
                  <span className="score-title-text" style={{ fontSize: '0.9rem' }}>Growth Score</span>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '3rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                    {selectedStock.growth_score}
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>out of 100</span>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div className="modal-section-title">Fundamental Profile</div>
                  <div className="card-metrics-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', padding: '1rem' }}>
                    <div className="metric-box">
                      <span className="metric-label" style={{ fontSize: '0.75rem' }}>Forward P/E</span>
                      <span className="metric-val" style={{ fontSize: '1.2rem' }}>{formatPE(selectedStock.forward_pe)}</span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label" style={{ fontSize: '0.75rem' }}>Revenue Growth</span>
                      <span className="metric-val" style={{ fontSize: '1.2rem' }}>{formatGrowth(selectedStock.revenue_growth)}</span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label" style={{ fontSize: '0.75rem' }}>Debt / Equity</span>
                      <span className="metric-val" style={{ fontSize: '1.2rem' }}>{formatDebt(selectedStock.debt_to_equity)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* LLM Key Insight */}
              <div>
                <div className="modal-section-title">Autonomous Insight</div>
                <div className="glass-panel" style={{ background: 'rgba(255, 255, 255, 0.02)', borderLeft: '3px solid var(--accent-cyan)', padding: '1.25rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
                  {selectedStock.key_insight}
                </div>
              </div>

              {/* News Headlines */}
              <div>
                <div className="modal-section-title">Ingested Market Signals (headlines)</div>
                {selectedStock.headlines && selectedStock.headlines.length > 0 ? (
                  <div className="headlines-list">
                    {selectedStock.headlines.map((headline, idx) => (
                      <div className="headline-item" key={idx}>
                        <span className="headline-bullet">✦</span>
                        <span>{headline}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No recent news headlines available for this ticker.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
