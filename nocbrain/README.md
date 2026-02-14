# NOCBrain v0.1

LLM-powered alert correlation system that integrates with Zabbix, correlates alerts, generates probable root cause suggestions using LLM, and exposes a REST API + minimal dashboard.

## Architecture

```
Zabbix API
   ↓
Ingestion Worker (FastAPI)
   ↓
PostgreSQL
   ↓
Correlation Engine
   ↓
LLM Root Cause Engine
   ↓
REST API
   ↓
React Frontend
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Zabbix server (for integration)
- OpenAI API key (for LLM analysis)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nocbrain
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your configuration:
```env
# Database
DATABASE_URL=postgresql+asyncpg://nocbrain:nocbrain_password@localhost:5432/nocbrain
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars

# Zabbix Integration
ZABBIX_URL=http://your-zabbix-server/zabbix/api_jsonrpc.php
ZABBIX_USER=Admin
ZABBIX_PASSWORD=zabbix_password

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-3.5-turbo
```

4. Start the system:
```bash
docker compose up --build
```

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default User

The system creates a default user:
- Username: `admin`
- Password: `admin123`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://nocbrain:nocbrain_password@localhost:5432/nocbrain` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT signing key | `your-secret-key-change-in-production` |
| `ZABBIX_URL` | Zabbix API endpoint | None |
| `ZABBIX_USER` | Zabbix username | None |
| `ZABBIX_PASSWORD` | Zabbix password | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `LLM_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |

### Zabbix Setup

1. Ensure Zabbix API is accessible
2. Create a user with API access permissions
3. Configure the Zabbix URL and credentials in `.env`

The system will automatically:
- Pull active problems from Zabbix every 60 seconds
- Convert them to internal alerts
- Correlate alerts into incidents

## API Usage

### Authentication

All endpoints except `/auth/login` require JWT authentication:

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Endpoints

#### Get Incidents
```bash
curl -X GET http://localhost:8000/incidents/ \
  -H "Authorization: Bearer <token>"
```

#### Get Incident Details
```bash
curl -X GET http://localhost:8000/incidents/<incident-id> \
  -H "Authorization: Bearer <token>"
```

#### Analyze Incident with AI
```bash
curl -X POST http://localhost:8000/incidents/<incident-id>/analyze \
  -H "Authorization: Bearer <token>"
```

#### Close Incident
```bash
curl -X POST http://localhost:8000/incidents/<incident-id>/close \
  -H "Authorization: Bearer <token>"
```

#### Get Alerts
```bash
curl -X GET http://localhost:8000/alerts/ \
  -H "Authorization: Bearer <token>"
```

## Correlation Rules

The system uses rule-based correlation (v0.1):

- Group alerts by host
- If more than 5 alerts from same host within 5 minutes → Create incident
- Attach alerts to existing incidents for the same host

## LLM Integration

The system uses OpenAI API for root cause analysis:

```python
# Prompt template
"You are a senior NOC engineer.
Given these alerts:
{alert_list}
Suggest the most probable root cause in 5 concise sentences.
Focus on the most likely technical issue causing these alerts.
Be specific and actionable."
```

## Database Schema

### Alerts
- `id` (UUID)
- `host` (string)
- `severity` (string)
- `message` (text)
- `timestamp` (datetime)
- `raw_payload` (jsonb)
- `incident_id` (UUID, nullable)

### Incidents
- `id` (UUID)
- `host` (string)
- `created_at` (datetime)
- `status` (enum: open/closed)
- `root_cause_summary` (text, nullable)
- `llm_explanation` (text, nullable)

### Users
- `id` (UUID)
- `username` (string)
- `hashed_password` (string)

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Database Migrations

The system uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

- Backend logs: Available in Docker container logs
- Frontend logs: Available in browser console and Docker container logs

## Security

- JWT-based authentication
- CORS restricted to frontend URL
- Environment-based configuration
- No hardcoded secrets
- Basic rate limiting

## Production Deployment

### Security Considerations

1. Change default passwords
2. Use strong SECRET_KEY
3. Configure proper CORS origins
4. Use HTTPS in production
5. Set up proper firewall rules

### Scaling

- PostgreSQL: Use managed database service
- Redis: Use Redis Cluster for high availability
- Backend: Deploy multiple instances behind load balancer
- Frontend: Deploy to CDN or static hosting

## Troubleshooting

### Common Issues

1. **Zabbix Connection Failed**
   - Verify Zabbix URL and credentials
   - Check network connectivity
   - Ensure Zabbix API is enabled

2. **LLM Analysis Failed**
   - Verify OpenAI API key
   - Check API quota
   - Review error logs

3. **Database Connection Failed**
   - Verify PostgreSQL is running
   - Check connection string
   - Ensure database exists

### Logs

```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs backend
docker compose logs frontend
docker compose logs postgres
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Docker logs
3. Create an issue in the repository
