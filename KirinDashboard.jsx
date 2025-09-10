import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './KirinDashboard.css';

// Cybersecurity Dashboard Implementation
const KirinSecurityDashboard = () => {
  const [criticalAlerts, setCriticalAlerts] = useState([]);
  const [liveData, setLiveData] = useState([]);
  const [threatLevel, setThreatLevel] = useState('medium');
  
  return (
    <div className="kirin-dashboard">
      {/* Critical Alert Banner */}
      <CriticalAlertBanner alerts={criticalAlerts} />
      
      {/* Main Layout Grid */}
      <div className="dashboard-grid">
        {/* Threat Level Indicator */}
        <ThreatLevelIndicator level={threatLevel} />
        
        {/* Sidebar */}
        <aside className="control-sidebar">
          <FilterPanel />
        </aside>
        
        {/* Main Content */}
        <main className="main-content">
          <RealTimeFeed data={liveData} />
          <VulnerabilityGrid />
        </main>
        
        {/* Detail Panel */}
        <aside className="detail-panel">
          <VulnerabilityDetails />
        </aside>
      </div>
    </div>
  );
};

// Critical Alert Banner Component
const CriticalAlertBanner = ({ alerts }) => {
  if (!alerts.length) return null;
  
  return (
    <motion.div 
      className="critical-banner"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className="alert-pulse" />
      <span className="alert-icon">[!!!]</span>
      <span className="alert-text">
        CRITICAL: {alerts[0].title} - {alerts[0].affected_tools.join(', ')}
      </span>
      <button className="alert-action">INVESTIGATE</button>
    </motion.div>
  );
};

// Real-Time Terminal Feed
const RealTimeFeed = ({ data }) => {
  const feedRef = useRef(null);
  const [isPaused, setIsPaused] = useState(false);
  
  useEffect(() => {
    if (!isPaused && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [data, isPaused]);
  
  return (
    <div className="terminal-feed">
      <div className="terminal-header">
        <span className="terminal-title">VULNERABILITY_STREAM</span>
        <div className="terminal-controls">
          <button onClick={() => setIsPaused(!isPaused)}>
            {isPaused ? '▶' : '❚❚'}
          </button>
        </div>
      </div>
      <div 
        className="terminal-body" 
        ref={feedRef}
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <AnimatePresence>
          {data.map((entry, index) => (
            <motion.div
              key={entry.id}
              className={`terminal-line severity-${entry.severity}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
            >
              <span className="timestamp">[{entry.timestamp}]</span>
              <span className="severity-indicator">
                {entry.severity === 'critical' ? '[!!!]' : 
                 entry.severity === 'high' ? '[!!]' : 
                 entry.severity === 'medium' ? '[!]' : '[·]'}
              </span>
              <span className="entry-text">{entry.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Vulnerability Card Component
const VulnerabilityCard = ({ vulnerability }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <motion.div 
      className={`vuln-card severity-${vulnerability.severity}`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="card-header">
        <div className="severity-strip" />
        <div className="card-id">{vulnerability.cve_id}</div>
        <div className="card-timestamp">{vulnerability.discovery_date}</div>
      </div>
      
      <div className="card-body">
        <h3 className="card-title">{vulnerability.title}</h3>
        
        <div className="affected-tools">
          {vulnerability.affected_tools.map(tool => (
            <span key={tool} className="tool-tag">{tool.toUpperCase()}</span>
          ))}
        </div>
        
        <div className="attack-vectors">
          {vulnerability.attack_vectors.map(vector => (
            <span key={vector} className="vector-badge">
              <span className="vector-icon">⚠</span>
              {vector}
            </span>
          ))}
        </div>
        
        <div className="card-metrics">
          <div className="metric">
            <span className="metric-label">CVSS</span>
            <span className="metric-value">{vulnerability.cvss_score}</span>
          </div>
          <div className="metric">
            <span className="metric-label">RISK</span>
            <span className="metric-value">{vulnerability.risk_score}</span>
          </div>
        </div>
      </div>
      
      <div className="card-footer">
        <div className="remediation-status">
          {vulnerability.kirin_remediation_available ? (
            <span className="status-available">REMEDIATION READY</span>
          ) : (
            <span className="status-pending">ANALYSIS REQUIRED</span>
          )}
        </div>
        <div className="card-actions">
          <button className="btn-primary">REMEDIATE</button>
          <button className="btn-ghost">DETAILS</button>
        </div>
      </div>
    </motion.div>
  );
};

// Threat Level Indicator
const ThreatLevelIndicator = ({ level }) => {
  const levels = ['low', 'medium', 'high', 'critical'];
  const currentIndex = levels.indexOf(level);
  
  return (
    <div className="threat-indicator">
      <div className="threat-bar">
        {levels.map((l, index) => (
          <div 
            key={l}
            className={`threat-segment ${index <= currentIndex ? 'active' : ''} level-${l}`}
          >
            <motion.div 
              className="threat-pulse"
              animate={{ opacity: index <= currentIndex ? [0.5, 1, 0.5] : 0 }}
              transition={{ duration: 2 - (index * 0.3), repeat: Infinity }}
            />
          </div>
        ))}
      </div>
      <div className="threat-label">
        THREAT LEVEL: <span className={`level-${level}`}>{level.toUpperCase()}</span>
      </div>
    </div>
  );
};

// Statistics Grid
const StatisticsGrid = () => {
  return (
    <div className="stats-grid">
      <StatCard
        title="CRITICAL VULNS"
        value="12"
        change="+3"
        trend="up"
        color="critical"
      />
      <StatCard
        title="UNPATCHED"
        value="47"
        change="-5"
        trend="down"
        color="high"
      />
      <StatCard
        title="REMEDIATED"
        value="238"
        change="+12"
        trend="up"
        color="success"
      />
      <StatCard
        title="AVG RESPONSE"
        value="4.2m"
        change="-1.3m"
        trend="down"
        color="info"
      />
    </div>
  );
};

// Stat Card Component
const StatCard = ({ title, value, change, trend, color }) => {
  return (
    <motion.div 
      className={`stat-card color-${color}`}
      whileHover={{ y: -2 }}
    >
      <div className="stat-header">{title}</div>
      <div className="stat-value">
        <motion.span
          key={value}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {value}
        </motion.span>
      </div>
      <div className={`stat-change trend-${trend}`}>
        <span className="change-icon">{trend === 'up' ? '▲' : '▼'}</span>
        <span className="change-value">{change}</span>
      </div>
      <div className="stat-sparkline">
        {/* Mini chart visualization */}
        <svg viewBox="0 0 100 30" className="sparkline">
          <polyline
            points="0,25 20,20 40,22 60,15 80,18 100,10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
        </svg>
      </div>
    </motion.div>
  );
};

// Filter Panel Component
const FilterPanel = () => {
  const [filters, setFilters] = useState({
    tools: [],
    severity: [],
    timeRange: '24h'
  });
  
  return (
    <div className="filter-panel">
      <div className="filter-header">
        <span className="filter-title">FILTERS</span>
        <button className="clear-filters">CLEAR</button>
      </div>
      
      <div className="filter-section">
        <div className="section-title">SEVERITY</div>
        <div className="filter-options">
          {['critical', 'high', 'medium', 'low'].map(level => (
            <label key={level} className="filter-option">
              <input type="checkbox" />
              <span className={`severity-label level-${level}`}>
                {level.toUpperCase()}
              </span>
            </label>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <div className="section-title">AI TOOLS</div>
        <div className="filter-options">
          {['cursor', 'copilot', 'codewhisperer', 'tabnine'].map(tool => (
            <label key={tool} className="filter-option">
              <input type="checkbox" />
              <span className="tool-label">{tool.toUpperCase()}</span>
            </label>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <div className="section-title">TIME RANGE</div>
        <select className="time-select">
          <option value="1h">LAST HOUR</option>
          <option value="24h">LAST 24 HOURS</option>
          <option value="7d">LAST 7 DAYS</option>
          <option value="30d">LAST 30 DAYS</option>
        </select>
      </div>
    </div>
  );
};

// Network Graph Visualization
const NetworkGraph = () => {
  return (
    <div className="network-graph">
      <div className="graph-header">
        <span className="graph-title">VULNERABILITY NETWORK</span>
        <div className="graph-controls">
          <button className="zoom-in">+</button>
          <button className="zoom-out">-</button>
          <button className="reset-view">⟲</button>
        </div>
      </div>
      <div className="graph-canvas">
        {/* D3.js or similar visualization would go here */}
        <svg className="network-svg">
          {/* Network nodes and edges */}
        </svg>
      </div>
    </div>
  );
};

// Code Diff Viewer
const CodeDiffViewer = ({ vulnerable, patched }) => {
  return (
    <div className="code-diff">
      <div className="diff-header">
        <span className="diff-title">VULNERABILITY DIFF</span>
        <button className="copy-code">COPY PATCH</button>
      </div>
      <div className="diff-content">
        <div className="diff-pane vulnerable">
          <div className="pane-header">VULNERABLE</div>
          <pre className="code-block">
            <code>{vulnerable}</code>
          </pre>
        </div>
        <div className="diff-pane patched">
          <div className="pane-header">PATCHED</div>
          <pre className="code-block">
            <code>{patched}</code>
          </pre>
        </div>
      </div>
    </div>
  );
};

export default KirinSecurityDashboard;
