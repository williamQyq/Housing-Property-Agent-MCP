# Housing Agent MCP - New Architecture

This project has been completely restructured to implement a modern microservices architecture with phone-based authentication, room management, and AI-powered assistance.

## 🏗️ Architecture Overview

The new architecture follows the design specified in `PROJECT.md` and implements the microservices pattern with the following components:

### Frontend
- **React + ai-sdk-ui**: Modern React application with AI-powered UI components
- **Phone Authentication**: OTP-based login system
- **Room Management**: Create rooms and invite users
- **Chat Interface**: AI assistant for housing-related tasks

### Backend Services (Go)
- **BFF (Backend for Frontend)**: Central API gateway with REST and GraphQL endpoints
- **Identity Service**: OTP authentication, user management, SMS integration
- **Orchestrator Service**: Room and invite management with PostgreSQL

### AI & Tools (Python)
- **Agent/MCP Service**: Tool execution with LLM integration and guardrails
- **Tool Registry**: Allowlisted tools for safe execution

### Payment Service (Java Spring Boot)
- **Payment Processing**: Stripe integration for rent and maintenance payments
- **Transaction Management**: Payment tracking and refunds

### Infrastructure
- **PostgreSQL**: Primary database for persistent storage
- **Redis**: Caching and session storage
- **Kubernetes**: Container orchestration and deployment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Go 1.21+
- Java 17+
- Python 3.11+
- Kubernetes cluster (optional)

### Local Development

1. **Start Infrastructure**:
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgres redis
   ```

2. **Start Backend Services**:
   ```bash
   # BFF Service
   cd services/bff
   go run main.go

   # Identity Service
   cd services/identity
   go run main.go

   # Orchestrator Service
   cd services/orchestrator
   go run main.go

   # Agent/MCP Service
   cd services/agent-mcp
   pip install -r requirements.txt
   python main.py

   # Payment Service
   cd services/payment-service
   mvn spring-boot:run
   ```

3. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Kubernetes Deployment

1. **Build Docker Images**:
   ```bash
   # Build all services
   docker build -t housing/bff-service:latest ./services/bff
   docker build -t housing/identity-service:latest ./services/identity
   docker build -t housing/orchestrator-service:latest ./services/orchestrator
   docker build -t housing/agent-mcp-service:latest ./services/agent-mcp
   docker build -t housing/payment-service:latest ./services/payment-service
   docker build -t housing/frontend:latest ./frontend
   ```

2. **Deploy to Kubernetes**:
   ```bash
   # Apply all manifests
   kubectl apply -f k8s/
   ```

## 📁 Project Structure

```
Housing-Agent-MCP/
├── frontend/                    # React + ai-sdk-ui application
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── pages/             # Page components
│   │   └── hooks/             # Custom React hooks
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── bff/                   # Backend for Frontend (Go)
│   │   ├── internal/
│   │   │   ├── config/        # Configuration
│   │   │   ├── handlers/      # HTTP handlers
│   │   │   ├── middleware/    # Middleware
│   │   │   ├── models/        # Data models
│   │   │   └── services/      # Business logic
│   │   └── main.go
│   ├── identity/              # Identity Service (Go)
│   │   ├── internal/
│   │   │   ├── config/        # Configuration
│   │   │   ├── handlers/      # HTTP handlers
│   │   │   ├── services/      # Business logic
│   │   │   ├── models/        # Data models
│   │   │   └── utils/         # Utilities
│   │   └── main.go
│   ├── orchestrator/          # Orchestrator Service (Go)
│   │   ├── internal/
│   │   │   ├── config/        # Configuration
│   │   │   ├── handlers/      # HTTP handlers
│   │   │   ├── services/      # Business logic
│   │   │   ├── models/        # Data models
│   │   │   └── database/      # Database setup
│   │   └── main.go
│   ├── agent-mcp/             # Agent/MCP Service (Python)
│   │   ├── main.py
│   │   └── requirements.txt
│   └── payment-service/       # Payment Service (Java Spring Boot)
│       ├── src/main/java/com/housing/payment/
│       │   ├── controller/    # REST controllers
│       │   ├── service/       # Business logic
│       │   ├── model/         # Data models
│       │   └── repository/    # Data access
│       ├── pom.xml
│       └── Dockerfile
├── k8s/                       # Kubernetes manifests
│   ├── bff/                   # BFF service manifests
│   ├── identity/              # Identity service manifests
│   ├── orchestrator/          # Orchestrator service manifests
│   ├── agent-mcp/             # Agent/MCP service manifests
│   ├── payment-service/       # Payment service manifests
│   ├── frontend/              # Frontend manifests
│   ├── postgres/              # PostgreSQL manifests
│   ├── redis/                 # Redis manifests
│   └── secrets.yaml           # Kubernetes secrets
└── data/legacy/               # Preserved SQLite data from legacy system
    ├── mcp_servers/
    │   └── mcp_filesystem_server.py
    └── data/
```

## 🔧 API Endpoints

### BFF Service (Port 8080)
- `POST /api/v1/auth/otp/start` - Start OTP authentication
- `POST /api/v1/auth/otp/verify` - Verify OTP code
- `POST /api/v1/rooms` - Create room
- `GET /api/v1/rooms` - List user's rooms
- `POST /api/v1/rooms/{id}/invites` - Create room invite
- `POST /api/v1/invites/{token}/accept` - Accept room invite
- `POST /api/v1/agent/execute` - Execute AI tool
- `POST /graphql` - GraphQL endpoint

### Identity Service (Port 8081)
- `POST /api/v1/otp/start` - Start OTP process
- `POST /api/v1/otp/verify` - Verify OTP code

### Orchestrator Service (Port 8082)
- `POST /api/v1/rooms` - Create room
- `GET /api/v1/rooms` - List rooms
- `POST /api/v1/rooms/{id}/invites` - Create invite
- `POST /api/v1/invites/{token}/accept` - Accept invite

### Agent/MCP Service (Port 8083)
- `GET /tools` - Get available tools
- `POST /execute` - Execute tool

### Payment Service (Port 8084)
- `POST /api/v1/payments` - Create payment
- `GET /api/v1/payments/{id}` - Get payment
- `POST /api/v1/payments/{id}/confirm` - Confirm payment
- `POST /api/v1/payments/{id}/refund` - Refund payment

## 🧪 Testing

The project includes comprehensive test suites for all services:

### Go Services
```bash
cd services/bff
go test ./...

cd services/identity
go test ./...

cd services/orchestrator
go test ./...
```

### Python Service
```bash
cd services/agent-mcp
python -m pytest
```

### Java Service
```bash
cd services/payment-service
mvn test
```

### Frontend
```bash
cd frontend
npm test
```

## 🔐 Security

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: OTP request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **CORS**: Properly configured cross-origin requests
- **Secrets Management**: Kubernetes secrets for sensitive data

## 📊 Monitoring

All services include:
- Health check endpoints
- Structured logging
- Resource limits
- Liveness and readiness probes

## 🚀 Deployment

### Local Development
Use Docker Compose for local development with all services.

### Production
Deploy to Kubernetes using the provided manifests in the `k8s/` directory.

## 🔄 Migration from Old Architecture

The old architecture has been completely replaced:
- ✅ Removed left panel components from frontend
- ✅ Cleaned up redundant code
- ✅ Implemented new microservices architecture
- ✅ Added comprehensive testing
- ✅ Created Kubernetes deployment configurations
- ✅ Implemented payment services with Java Spring Boot

## 📝 Next Steps

1. **Environment Setup**: Configure production environment variables
2. **Database Migration**: Set up production database
3. **Monitoring**: Add comprehensive monitoring and alerting
4. **CI/CD**: Set up continuous integration and deployment
5. **Documentation**: Add API documentation with OpenAPI/Swagger

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
