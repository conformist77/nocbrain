# NOCBrain v0.1 Project Structure

```
nocbrain/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration and settings
│   │   ├── db.py                  # Database models and connection
│   │   ├── models.py               # Pydantic models for API
│   │   ├── auth.py                # JWT authentication utilities
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── alerts.py          # Alert management endpoints
│   │   │   └── incidents.py       # Incident management endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── zabbix_client.py   # Zabbix integration client
│   │       ├── correlation.py      # Alert correlation engine
│   │       ├── llm_service.py     # LLM integration service
│   │       └── runbook.py         # Runbook management service
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                # Backend Docker configuration
│
├── frontend/
│   ├── public/
│   │   └── index.html            # HTML template
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.tsx         # Login component
│   │   │   ├── Dashboard.tsx     # Dashboard component
│   │   │   └── IncidentDetail.tsx # Incident detail component
│   │   ├── App.tsx               # Main React application
│   │   ├── App.css               # Application styles
│   │   ├── index.tsx             # React entry point
│   │   └── index.css             # Global styles
│   ├── package.json              # Node.js dependencies
│   └── Dockerfile                # Frontend Docker configuration
│
├── scripts/
│   └── init_db.py               # Database initialization script
│
├── docker-compose.yml            # Docker Compose configuration
├── .env.example                 # Environment variables template
├── README.md                    # Project documentation
└── PROJECT_TREE.md             # This file
```

## Key Components

### Backend Services
- **Zabbix Client**: Pulls active problems from Zabbix API
- **Correlation Engine**: Groups alerts into incidents based on rules
- **LLM Service**: Analyzes incidents using OpenAI API
- **Runbook Service**: Provides remediation steps and procedures

### API Endpoints
- `/auth/login` - JWT authentication
- `/alerts/` - Alert management
- `/incidents/` - Incident management
- `/incidents/{id}/analyze` - AI-powered analysis
- `/incidents/{id}/close` - Incident resolution

### Frontend Components
- **Login**: User authentication
- **Dashboard**: Incident list and overview
- **IncidentDetail**: Detailed incident view with AI analysis

### Database Tables
- **alerts**: Individual alert records from Zabbix
- **incidents**: Correlated alert groups
- **users**: Authentication and authorization

## Data Flow

1. Zabbix → Zabbix Client → PostgreSQL (alerts table)
2. Correlation Engine processes alerts → creates incidents
3. LLM Service analyzes incidents → root cause suggestions
4. Frontend displays incidents via REST API
5. Users can trigger AI analysis and close incidents
