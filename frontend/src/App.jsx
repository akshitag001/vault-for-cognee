import React, { useState, useEffect } from 'react';
import { Database, Search, ShieldAlert, FileText, Lock, Globe, AlertTriangle } from 'lucide-react';
import './index.css';

const API_URL = 'http://localhost:8000';

const apiFetch = async (endpoint, options = {}) => {
  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
  return res.json();
};

function IngestPanel() {
  const [content, setContent] = useState('');
  const [dataset, setDataset] = useState('demo_dataset');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await apiFetch('/ingest', {
        method: 'POST',
        body: JSON.stringify({ content, dataset_name: dataset }),
      });
      setResult(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2><Database className="inline-icon" size={24} style={{verticalAlign: 'text-bottom', marginRight: '8px'}} /> Ingest Data</h2>
      <p>Paste notes, API keys, or text below. Vault will intelligently classify and route it.</p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Dataset Name</label>
          <input value={dataset} onChange={(e) => setDataset(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Content</label>
          <textarea value={content} onChange={(e) => setContent(e.target.value)} required placeholder="Enter content here..." />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Submit to Memory'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: '1.5rem' }}>
          {result.routed_to === 'vault' ? (
            <div>
              <div className="badge vault">→ Routed to Vault (encrypted)</div>
              <p style={{marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--vault-color)'}}>
                Protected triggers: {result.matched_patterns.join(', ')}
              </p>
            </div>
          ) : (
            <div className="badge cognee">→ Routed to Cognee (knowledge graph)</div>
          )}
        </div>
      )}
    </div>
  );
}

function QueryPanel() {
  const [query, setQuery] = useState('');
  const [dataset, setDataset] = useState('demo_dataset');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const data = await apiFetch('/query', {
        method: 'POST',
        body: JSON.stringify({ query, dataset_name: dataset }),
      });
      setResults(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2><Search className="inline-icon" size={24} style={{verticalAlign: 'text-bottom', marginRight: '8px'}} /> Query Memory</h2>
      <p>Search across both standard semantic memory and encrypted vaults simultaneously.</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Dataset Name</label>
          <input value={dataset} onChange={(e) => setDataset(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Search Query</label>
          <input value={query} onChange={(e) => setQuery(e.target.value)} required placeholder="Search..." />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results && (
        <div className="query-grid">
          <div className="query-col">
            <div className="query-col-header" style={{color: 'var(--cognee-color)'}}>
              <Globe size={20} />
              <h3>Open Memory (Cognee)</h3>
            </div>
            {results.cognee_hits.length === 0 ? (
              <p>No results found.</p>
            ) : (
              results.cognee_hits.map((hit, i) => (
                <div key={i} className="result-card">{hit.content}</div>
              ))
            )}
          </div>
          
          <div className="query-col">
            <div className="query-col-header" style={{color: 'var(--vault-color)'}}>
              <Lock size={20} />
              <h3>Encrypted Vault</h3>
            </div>
            {results.vault_hits.length === 0 ? (
              <p>No results found.</p>
            ) : (
              results.vault_hits.map((hit, i) => (
                <div key={i} className="result-card decryption-container">
                  <div className="checking-wrapper">
                    <span className="checking-access">
                      <Lock size={16} /> checking access... 
                    </span>
                  </div>
                  <div className="decrypted-content">
                    <span style={{color: 'var(--vault-color)', display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600}}>🔓 Decrypted</span>
                    {hit.content}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AuditPanel() {
  const [dataset, setDataset] = useState('demo_dataset');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const data = await apiFetch(`/access-log/${dataset}`);
      setLogs(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="panel">
      <h2><FileText className="inline-icon" size={24} style={{verticalAlign: 'text-bottom', marginRight: '8px'}} /> Audit Log</h2>
      <p style={{color: 'var(--accent-color)', fontWeight: 500}}>
        Every access to your encrypted vault is logged. Queries are hashed, not stored in plaintext.
      </p>
      
      <form onSubmit={fetchLogs} style={{display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '2rem'}}>
        <div className="form-group" style={{marginBottom: 0, flex: 1}}>
          <label>Dataset Name</label>
          <input value={dataset} onChange={(e) => setDataset(e.target.value)} required />
        </div>
        <button type="submit" disabled={loading}>Refresh</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Query Hash</th>
            <th>Hits</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td><span className="hash">•••• ({log.query_hash.substring(0, 8)}...)</span></td>
              <td>{log.matched_doc_count}</td>
            </tr>
          ))}
          {logs.length === 0 && (
            <tr>
              <td colSpan="3" style={{textAlign: 'center', color: 'var(--text-muted)'}}>No audit logs found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ForgetPanel() {
  const [dataset, setDataset] = useState('demo_dataset');
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleForget = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const data = await apiFetch('/forget', {
        method: 'POST',
        body: JSON.stringify({ dataset_name: dataset }),
      });
      setMessage(data.message);
      setConfirming(false);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel danger-zone">
      <h2 style={{color: 'var(--danger-color)'}}><ShieldAlert className="inline-icon" size={24} style={{verticalAlign: 'text-bottom', marginRight: '8px'}} /> Forget Dataset</h2>
      <p>Cryptographically erase the Vault encryption keys. The ciphertexts will become permanently unreadable.</p>
      
      <div className="form-group" style={{maxWidth: '400px'}}>
        <label>Dataset to Destroy</label>
        <input value={dataset} onChange={(e) => setDataset(e.target.value)} required disabled={confirming} />
      </div>

      {!confirming ? (
        <button className="danger" onClick={() => setConfirming(true)}>
          Forget Dataset
        </button>
      ) : (
        <div className="confirm-warning">
          <h3 style={{color: 'var(--danger-color)'}}><AlertTriangle size={18} style={{verticalAlign: 'text-bottom'}} /> Are you sure?</h3>
          <p style={{fontSize: '0.9rem', marginBottom: '1rem'}}>This action destroys the keys and cannot be undone.</p>
          <div style={{display: 'flex', gap: '1rem'}}>
            <button className="danger" onClick={handleForget} disabled={loading}>
              {loading ? 'Destroying...' : 'Yes, erase permanently'}
            </button>
            <button style={{background: 'rgba(255,255,255,0.1)'}} onClick={() => setConfirming(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {message && (
        <p style={{marginTop: '1rem', color: 'var(--danger-color)', fontWeight: 600}}>
          {message}
        </p>
      )}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('ingest');

  return (
    <div>
      <h1 style={{textAlign: 'center'}}>Vault</h1>
      <p className="header-subtitle" style={{textAlign: 'center'}}>Privacy-Preserving Memory Layer on Cognee</p>
      
      <div className="tabs">
        <button className={`tab ${activeTab === 'ingest' ? 'active' : ''}`} onClick={() => setActiveTab('ingest')}>
          <Database size={18} /> Ingest
        </button>
        <button className={`tab ${activeTab === 'query' ? 'active' : ''}`} onClick={() => setActiveTab('query')}>
          <Search size={18} /> Query
        </button>
        <button className={`tab ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>
          <FileText size={18} /> Audit Log
        </button>
        <button className={`tab ${activeTab === 'forget' ? 'active' : ''}`} onClick={() => setActiveTab('forget')}>
          <ShieldAlert size={18} /> Forget
        </button>
      </div>

      {activeTab === 'ingest' && <IngestPanel />}
      {activeTab === 'query' && <QueryPanel />}
      {activeTab === 'audit' && <AuditPanel />}
      {activeTab === 'forget' && <ForgetPanel />}
    </div>
  );
}

export default App;
