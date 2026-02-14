import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Alert {
  id: string;
  severity: string;
  message: string;
  timestamp: string;
}

interface Incident {
  id: string;
  host: string;
  created_at: string;
  status: 'open' | 'closed';
  root_cause_summary?: string;
  llm_explanation?: string;
  alerts: Alert[];
}

interface IncidentDetailProps {
  user: { id: string; username: string };
}

const IncidentDetail: React.FC<IncidentDetailProps> = ({ user }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (id) {
      fetchIncident(id);
    }
  }, [id]);

  const fetchIncident = async (incidentId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/incidents/${incidentId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setIncident(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch incident');
    } finally {
      setLoading(false);
    }
  };

  const analyzeIncident = async () => {
    if (!incident) return;
    
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/incidents/${incident.id}/analyze`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh incident data
      await fetchIncident(incident.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const closeIncident = async () => {
    if (!incident) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/incidents/${incident.id}/close`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Refresh incident data
      await fetchIncident(incident.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to close incident');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case 'disaster':
      case 'high':
        return 'high';
      case 'average':
        return 'average';
      default:
        return 'warning';
    }
  };

  if (loading) {
    return <div className="loading">Loading incident...</div>;
  }

  if (error || !incident) {
    return (
      <div className="incident-detail">
        <div className="error">{error || 'Incident not found'}</div>
        <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="incident-detail">
      <div className="incident-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>Incident: {incident.host}</h1>
            <p><strong>Status:</strong> 
              <span className={`status ${incident.status}`}>
                {incident.status.toUpperCase()}
              </span>
            </p>
            <p><strong>Created:</strong> {formatDate(incident.created_at)}</p>
          </div>
          
          <div className="incident-actions">
            {incident.status === 'open' && (
              <>
                <button 
                  onClick={analyzeIncident} 
                  className="btn btn-primary"
                  disabled={analyzing}
                >
                  {analyzing ? <span className="loading-spinner"></span> : 'Analyze with AI'}
                </button>
                <button onClick={closeIncident} className="btn btn-success">
                  Close Incident
                </button>
              </>
            )}
            <button onClick={() => navigate('/dashboard')} className="btn btn-danger">
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="incident-content">
        {incident.root_cause_summary && (
          <div className="analysis-section">
            <h4>Root Cause Analysis</h4>
            <p><strong>Summary:</strong> {incident.root_cause_summary}</p>
            {incident.llm_explanation && (
              <p><strong>Explanation:</strong> {incident.llm_explanation}</p>
            )}
          </div>
        )}

        <div className="alerts-section">
          <h3>Alerts ({incident.alerts?.length || 0})</h3>
          {incident.alerts?.map((alert) => (
            <div key={alert.id} className={`alert-item ${getSeverityClass(alert.severity)}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{alert.severity.toUpperCase()}</strong>
                <span>{formatDate(alert.timestamp)}</span>
              </div>
              <p>{alert.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IncidentDetail;
