import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

export default function TickerCard({ analysis, onClick }) {
  const {
    ticker,
    date,
    growth_score,
    sentiment,
    forward_pe,
    revenue_growth,
    debt_to_equity,
    key_insight
  } = analysis;

  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Fetch historical data for this ticker to render sparkline
    fetch(`${API_BASE_URL}/api/analysis/history/${ticker}`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch history");
        return res.json();
      })
      .then(data => {
        setHistory(data);
      })
      .catch(err => console.error("Error fetching card history for", ticker, err));
  }, [ticker, date]); // Refresh when ticker or date changes (after pipeline runs)

  // Sentiment class mappings
  const sentimentClass = sentiment ? sentiment.toLowerCase() : 'neutral';
  
  // Radial Score configuration
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (growth_score / 100) * circumference;

  // Format metrics helpers
  const formatPE = (val) => val != null ? val.toFixed(2) : 'N/A';
  const formatGrowth = (val) => val != null ? `${(val * 100).toFixed(1)}%` : 'N/A';
  const formatDebt = (val) => val != null ? `${val.toFixed(1)}%` : 'N/A';

  // Render Sparkline SVG Path
  const renderSparkline = () => {
    if (history.length < 2) {
      return <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Accumulating trends...</span>;
    }

    const width = 120;
    const height = 30;
    const padding = 2;
    
    // Map score (1 to 100) and dates to X/Y
    const minScore = 1;
    const maxScore = 100;
    
    const points = history.map((item, idx) => {
      const x = padding + (idx / (history.length - 1)) * (width - 2 * padding);
      // SVG Y goes from 0 (top) to height (bottom). Score 100 is at top, Score 1 is at bottom.
      const y = height - padding - ((item.growth_score - minScore) / (maxScore - minScore)) * (height - 2 * padding);
      return { x, y };
    });

    const pathData = points.reduce((acc, p, idx) => {
      return acc + (idx === 0 ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`);
    }, '');

    // Area path for gradient fill
    const areaPathData = `${pathData} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`;

    return (
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id={`grad-${ticker}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={`var(--accent-cyan)`} stopOpacity="0.4" />
            <stop offset="100%" stopColor={`var(--accent-cyan)`} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPathData} fill={`url(#grad-${ticker})`} />
        <path d={pathData} fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="3" fill="var(--accent-cyan)" />
      </svg>
    );
  };

  return (
    <div 
      className={`glass-panel stock-card card-${sentimentClass}`}
      onClick={() => onClick(analysis)}
    >
      {/* Header Row */}
      <div className="card-header-row">
        <div>
          <div className="card-ticker-name">{ticker}</div>
          <div className="card-date">Analyzed: {date}</div>
        </div>
        <span className={`sentiment-badge ${sentimentClass}`}>{sentiment}</span>
      </div>

      {/* Growth Score Circle */}
      <div className="card-score-row">
        <div className="score-radial">
          <svg width="60" height="60" style={{ transform: 'rotate(-90deg)' }}>
            {/* Background Circle */}
            <circle
              cx="30"
              cy="30"
              r={radius}
              fill="transparent"
              stroke="rgba(255, 255, 255, 0.05)"
              strokeWidth="4"
            />
            {/* Progress Circle */}
            <circle
              cx="30"
              cy="30"
              r={radius}
              fill="transparent"
              stroke={`var(--${sentimentClass})`}
              strokeWidth="4"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
            />
          </svg>
          <span className="score-value">{growth_score}</span>
        </div>
        
        <div className="score-details-label">
          <span className="score-title-text">Growth Score</span>
          <span className="score-desc-text">
            {growth_score >= 70 ? 'Strong Growth' : growth_score >= 50 ? 'Moderate Growth' : 'High Risk'}
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="card-metrics-grid">
        <div className="metric-box">
          <span className="metric-label">Forward P/E</span>
          <span className="metric-val">{formatPE(forward_pe)}</span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Revenue Growth</span>
          <span className="metric-val">{formatGrowth(revenue_growth)}</span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Debt / Equity</span>
          <span className="metric-val">{formatDebt(debt_to_equity)}</span>
        </div>
      </div>

      {/* Key Insight Preview */}
      {key_insight && (
        <p className="card-insight">
          {key_insight}
        </p>
      )}

      {/* Sparkline Trend */}
      <div className="card-sparkline" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Score History</span>
          {renderSparkline()}
        </div>
      </div>
    </div>
  );
}
