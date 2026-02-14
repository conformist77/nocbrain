import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

interface Incident {
  id: string;
  host: string;
  created_at: string;
  status: 'open' | 'closed';
  root_cause_summary?: string;
  alerts: Array<{
    id: string;
    severity: string;
    message: string;
    timestamp: string;
  }>;
}

interface DashboardProps {
  user: { id: string; username: string };
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/incidents/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setIncidents(response.data.incidents);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch incidents');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityClass = (alerts: any[]) => {
    if (!alerts || alerts.length === 0) return '';
    const severities = alerts.map(a => a.severity);
    if (severities.includes('disaster') || severities.includes('high')) return 'high';
    if (severities.includes('average')) return 'average';
    return 'warning';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div>
        <nav className="nav">
          <h1>NOCBrain</h1>
          <div className="user-info">
            <span>{user.username}</span>
            <button onClick={onLogout}>Logout</button>
          </div>
        </nav>
        <div className="dashboard">
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <nav className="nav">
        <h1>NOCBrain</h1>
        <div className="user-info">
          <span>{user.username}</span>
          <button onClick={onLogout}>Logout</button>
        </div>
      </nav>
      
      <div className="dashboard">
        <h2>Incidents</h2>
        
        {error && <div className="error">{error}</div>}
        
        {incidents.length === 0 ? (
          <p>No incidents found.</p>
        ) : (
          <div className="incidents-grid">
            {incidents.map((incident) => (
              <div 
                key={incident.id} 
                className={`incident-card ${getSeverityClass(incident.alerts)}`}
              >
                <h3>{incident.host}</h3>
                
                <div className="incident-meta">
                  <span className={`status ${incident.status}`}>
                    {incident.status.toUpperCase()}
                  </span>
                  <span>{formatDate(incident.created_at)}</span>
                </div>
                
                {incident.root_cause_summary && (
                  <p><strong>Root Cause:</strong> {incident.root_cause_summary}</p>
                )}
                
                <p><strong>Alerts:</strong> {incident.alerts?.length || 0}</p>
                
                <div className="incident-actions">
                  <Link to={`/incidents/${incident.id}`} className="btn btn-primary">
                    View Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
