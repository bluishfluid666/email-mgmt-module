# Email Management API

A FastAPI-based REST API for email management using Microsoft Graph API.

## Features

- **User Management**: Get authenticated user information
- **Email Reading**: List inbox messages with pagination
- **Email Sending**: Send emails with text or HTML content
- **Authentication**: Automatic Microsoft Graph authentication at startup
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
DEBUG=true
```

### 2. Installation

#### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# OR use the convenience script
python run.py
```

#### Option B: Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### 3. Authentication

The application automatically handles Microsoft Graph authentication:
1. **Startup Authentication**: On server startup, the application will authenticate with Microsoft Graph. Look for the line "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code XXXXXXXXX to authenticate." in the server log.
2. **Device Code Flow**: You'll be prompted to visit a URL and enter a device code
3. **Sign In**: Complete the sign-in with your Microsoft account
4. **Grant Permissions**: Approve the requested permissions
5. **Ready to Use**: Once authenticated, all API endpoints are ready for use without further authentication

## Usage Examples

### Get User Information
```bash
curl -X GET "http://localhost:8001/api/v1/user"
```

### List Inbox Messages
```bash
curl -X GET "http://localhost:8001/api/v1/emails/inbox?limit=10"
```

### Send Email
```bash
curl -X POST "http://localhost:8001/api/v1/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Test Email",
    "body": "Hello from the API!",
    "body_type": "text"
  }'
```

**Note**: No authentication headers are required as the service is pre-authenticated at startup.

## Authentication Flow

The application uses a **singleton pattern** for Microsoft Graph authentication:

1. **Startup Authentication**: When the server starts, it initializes a single Graph service instance
2. **Device Code Authentication**: During startup, you'll see prompts to complete device code authentication
3. **Global Instance**: The authenticated service is stored globally and reused for all API requests
4. **No Per-Request Auth**: Subsequent API calls don't require individual authentication
5. **Session Persistence**: The authentication persists for the lifetime of the server process

### Startup Logs Example:
```
INFO - Initializing Graph service...
INFO - Attempting to authenticate with Microsoft Graph...
INFO - Successfully authenticated as: John Doe (john.doe@company.com)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLIENT_ID` | Azure application client ID | Required |
| `TENANT_ID` | Azure tenant ID | Required |
| `GRAPH_USER_SCOPES` | Graph API scopes | `User.Read Mail.Read Mail.Send` |
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
│   ├── auth.py              # Authentication (optional)
│   ├── graph_service.py     # Graph API service
│   ├── dependencies.py     # Dependency injection
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

1. **Authentication**: Microsoft Graph authentication is handled at application startup
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure CORS appropriately for your frontend domains
4. **Scopes**: Only request minimum required Graph API scopes
5. **Secrets**: Never commit secrets to version control
6. **Access Control**: Consider implementing additional access controls for production use

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
