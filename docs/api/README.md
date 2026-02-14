# NOCbRAIN API Documentation

## Overview
NOCbRAIN provides a comprehensive REST API for network monitoring, security analysis, and AI-powered operations.

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.nocbrain.com/api/v1
```

## Authentication
All API requests require authentication using JWT tokens:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     https://api.nocbrain.com/api/v1/endpoint
```

## Multi-tenancy
All requests must include the tenant ID header:

```bash
curl -H "X-Tenant-ID: your-tenant-uuid" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://api.nocbrain.com/api/v1/tenant/dashboard
```

## API Endpoints

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - User logout

### Network Monitoring
- `GET /network/devices` - List network devices
- `POST /network/devices` - Add new device
- `GET /network/metrics` - Get network metrics
- `POST /network/scan` - Network discovery scan

### Security Analysis
- `POST /security/analyze` - Analyze security event
- `GET /security/threats` - List detected threats
- `POST /security/rules` - Add security rule
- `GET /security/dashboard` - Security dashboard

### AI Core Engine
- `POST /core/analyze-log` - AI-powered log analysis
- `POST /core/knowledge/query` - Query knowledge base
- `POST /core/incident/plan` - Generate incident response plan
- `GET /core/status` - AI engine status

### Tenant Management
- `GET /tenant/dashboard` - Tenant-specific dashboard
- `POST /tenant/analyze-log` - Tenant-isolated log analysis
- `POST /tenant/knowledge/query` - Tenant knowledge search
- `GET /tenant/stats` - Tenant statistics

## Rate Limiting
- Standard endpoints: 100 requests per minute
- AI endpoints: 50 requests per minute
- Bulk operations: 10 requests per minute

## Error Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

## SDK Examples

### Python
```python
import requests

# Authentication
response = requests.post('https://api.nocbrain.com/api/v1/auth/login', json={
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['access_token']

# API Request
headers = {
    'Authorization': f'Bearer {token}',
    'X-Tenant-ID': 'your-tenant-uuid',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.nocbrain.com/api/v1/tenant/dashboard',
    headers=headers
)
```

### JavaScript
```javascript
// Authentication
const loginResponse = await fetch('https://api.nocbrain.com/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'your_username',
        password: 'your_password'
    })
});
const { access_token } = await loginResponse.json();

// API Request
const response = await fetch('https://api.nocbrain.com/api/v1/tenant/dashboard', {
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'X-Tenant-ID': 'your-tenant-uuid',
        'Content-Type': 'application/json'
    }
});
const data = await response.json();
```

## WebSocket API
Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('wss://api.nocbrain.com/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

## OpenAPI Specification
Full API specification available at:
- Development: http://localhost:8000/docs
- Production: https://api.nocbrain.com/docs
