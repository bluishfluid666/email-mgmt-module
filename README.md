# Email Management API

A FastAPI-based REST API for email management using Microsoft Graph API.

## Features

- **User Management**: Get authenticated user information
- **Email Reading**: List inbox messages with pagination
- **Email Sending**: Send emails with text or HTML content
- **Authentication**: API key-based authentication
- **Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Health Checks**: Built-in health monitoring
- **Docker Support**: Containerized deployment

## API Endpoints

### Core Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/user` - Get authenticated user info
- `GET /api/v1/emails/inbox` - List inbox messages
- `POST /api/v1/emails/send` - Send email
- `GET /api/v1/auth/token` - Get token information

### Documentation

- `GET /docs` - Interactive API documentation (Swagger)
- `GET /redoc` - Alternative API documentation

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```env
CLIENT_ID=your-azure-client-id
TENANT_ID=your-azure-tenant-id
GRAPH_USER_SCOPES=User.Read Mail.Read Mail.Send
API_KEY=your-secure-api-key
```

### 2. Installation

#### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option B: Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### 3. First Run Authentication

On first run, you'll need to authenticate with Microsoft Graph:
1. The application will prompt for device code authentication
2. Visit the provided URL and enter the code
3. Sign in with your Microsoft account
4. Grant the requested permissions

## Usage Examples

### Get User Information
```bash
curl -X GET "http://localhost:8000/api/v1/user" \
  -H "Authorization: Bearer your-api-key"
```

### List Inbox Messages
```bash
curl -X GET "http://localhost:8000/api/v1/emails/inbox?limit=10" \
  -H "Authorization: Bearer your-api-key"
```

### Send Email
```bash
curl -X POST "http://localhost:8000/api/v1/emails/send" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Test Email",
    "body": "Hello from the API!",
    "body_type": "text"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLIENT_ID` | Azure application client ID | Required |
| `TENANT_ID` | Azure tenant ID | Required |
| `GRAPH_USER_SCOPES` | Graph API scopes | `User.Read Mail.Read Mail.Send` |
| `API_KEY` | API authentication key | Required |
| `APP_NAME` | Application name | `Email Management API` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Enable debug mode | `false` |

### Azure App Registration

Ensure your Azure app registration has:
1. Correct redirect URIs configured
2. Required API permissions granted
3. Admin consent provided for organizational scopes

## Development

### Project Structure
```
email-mgmt-module/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Authentication
│   ├── graph_service.py     # Graph API service
│   └── api/
│       ├── __init__.py
│       └── routes.py        # API endpoints
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── config.cfg              # Legacy config file
└── README.md               # This file
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

## Security Considerations

1. **API Key**: Use a strong, unique API key in production
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure CORS appropriately for your frontend domains
4. **Scopes**: Only request minimum required Graph API scopes
5. **Secrets**: Never commit secrets to version control

## Monitoring

The API includes:
- Health check endpoint at `/api/v1/health`
- Structured logging
- Error handling with appropriate HTTP status codes
- Docker health checks

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure Azure app registration is correctly configured
2. **Permission Errors**: Verify Graph API permissions are granted and consented
3. **Token Errors**: Check if device code authentication is completed

### Logs

Check application logs for detailed error information:
```bash
# Docker logs
docker-compose logs email-api

# Local development
# Logs are printed to console
```

## License

This project is licensed under the MIT License.
