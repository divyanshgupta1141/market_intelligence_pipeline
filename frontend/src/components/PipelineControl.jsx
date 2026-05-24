import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config';

export default function PipelineControl({ watchlist, onRunCompleted }) {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const consoleEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Poll for logs from the backend
  const fetchLogs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipeline/logs`);
      if (!response.ok) throw new Error("Failed to fetch logs");
      const data = await response.json();
      
      setLogs(data.logs || []);
      setRunning(data.running);
      
      // If the backend says the pipeline finished running, stop polling
      if (!data.running && pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
        onRunCompleted(); // Trigger parent dashboard refresh
      }
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  };

  // Scroll to bottom of terminal
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleRunPipeline = async () => {
    if (running) return;
    
    setRunning(true);
    setLogs(["[SYSTEM] Initializing background pipeline run request..."]);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers: null }) // Run for all watched tickers
      });
      
      if (!response.ok) throw new Error("Failed to run pipeline");
      
      // Start polling logs every 1 second
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(fetchLogs, 1000);
      
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] Failed to start pipeline: ${err.message}`]);
      setRunning(false);
    }
  };

  // Parse log message to assign CSS color class
  const getLogClass = (line) => {
    if (line.includes('[ERROR]') || line.includes('Traceback')) return 'console-line error';
    if (line.includes('[WARNING]')) return 'console-line warning';
    if (line.includes('Success') || line.includes('complete') || line.includes('Successfully')) return 'console-line success';
    return 'console-line info';
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="panel-title">
        <span>⚙️</span> Engine Control
      </div>

      <button 
        type="button" 
        className="btn btn-primary" 
        onClick={handleRunPipeline}
        disabled={running || watchlist.length === 0}
        style={{ width: '100%', py: '1rem' }}
      >
        {running ? (
          <>
            <span className="spin">🌀</span> Running Intelligence Pipeline...
          </>
        ) : (
          'Trigger Watchlist Analysis'
        )}
      </button>

      {watchlist.length === 0 && (
        <div style={{ color: 'var(--neutral)', fontSize: '0.8rem', textAlign: 'center' }}>
          ⚠️ Watchlist is empty. Add tickers to enable analysis.
        </div>
      )}

      {/* Simulated Terminal logs */}
      {(logs.length > 0 || running) && (
        <div className="glass-panel console-panel">
          <div className="console-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: running ? 'var(--neutral)' : 'var(--bullish)' }}></span>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                {running ? 'Execution Terminal (Active)' : 'Execution Terminal (Offline)'}
              </span>
            </div>
            <button 
              type="button" 
              className="btn-icon-only" 
              style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}
              onClick={() => setLogs([])}
              disabled={running}
            >
              Clear Console
            </button>
          </div>
          <div className="console-body">
            {logs.map((line, idx) => (
              <div key={idx} className={getLogClass(line)}>
                {line}
              </div>
            ))}
            <div ref={consoleEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
