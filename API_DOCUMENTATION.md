# StoreOps REST API - Complete Documentation

**Retail Operations Management Platform**

A production-grade REST API for managing retail store operations, built with **Python 3.12**, **FastAPI**, and clean architecture principles.

## 📋 Overview

StoreOps is a comprehensive platform for managing:

- **Activities**: Operational tasks, compliance audits, restocking, planogram updates
- **Programmes**: Store initiatives, campaigns, rollouts  
- **Staff**: Store employees, department leads, managers, regional managers
- **Alerts**: Notifications, escalations, SLA breach alerts
- **Reports**: Store metrics, regional summaries, department performance

## 🏗️ Architecture

### Three-Layer Clean Architecture

```
Routes Layer (HTTP handlers)
    ↓
Service Layer (Business logic, validation, events)
    ↓
Repository Layer (Data access)
```

**Key Principles:**
- ✅ Routes call Services only
- ✅ Services call Repositories only
- ✅ Repositories have no business logic
- ✅ No circular imports between modules
- ✅ Cross-module communication via EventBus only
- ✅ All errors are typed (no raw exceptions)

### Module Structure

Each module includes:
```
module/
├── models.py       # Pydantic models
├── repository.py   # Data access
├── service.py      # Business logic
├── routes.py       # HTTP endpoints
└── __init__.py
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
python -m uvicorn src.main:app --reload
```

Visit `http://localhost:8000/docs` for Swagger UI.

### Docker

```bash
docker-compose up
```

## 📊 API Endpoints

### Activities `/api/v1/activities`
- `POST /tasks` - Create task
- `GET /tasks/{id}` - Get task
- `GET /tasks` - List tasks
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `GET /tasks/status/{status}` - Filter by status
- `GET /users/{id}/tasks` - Get user's tasks

### Programmes `/api/v1/programmes`
- `POST /` - Create
- `GET /{id}` - Get
- `GET /` - List
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete

### Staff `/api/v1/staff`
- `POST /` - Create
- `GET /{id}` - Get
- `GET /` - List
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete
- `GET /stores/{store_id}` - Get store staff

### Alerts `/api/v1/alerts`
- `POST /` - Create
- `GET /{id}` - Get
- `GET /` - List
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete
- `GET /status/{status}` - Filter by status
- `GET /severity/{severity}` - Filter by severity

### Reports `/api/v1/reports`
- `POST /` - Create
- `GET /{id}` - Get
- `GET /` - List
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete
- `GET /type/{type}` - Filter by type

## 🔄 Event Bus

Modules communicate via async event bus - no direct cross-module calls.

**Event Types:**
- `TASK_CREATED`, `TASK_COMPLETED`, `TASK_OVERDUE`, `TASK_ASSIGNED`
- `PROGRAMME_CREATED`, `PROGRAMME_STARTED`, `PROGRAMME_COMPLETED`
- `STAFF_ONBOARDED`, `STAFF_OFFBOARDED`
- `SLA_BREACH`, `CRITICAL_ALERT`, `ESCALATION_NEEDED`
- `REPORT_GENERATED`

## ❌ Error Handling

All errors are typed (AppError, ValidationError, NotFoundError, BusinessRuleViolationError, ConflictError).

**Error Response Format:**
```json
{
  "error_code": "ERROR_TYPE",
  "message": "Human readable message",
  "details": { "key": "value" }
}
```

## 🧪 Testing

```bash
pytest              # Run all tests
pytest --cov        # With coverage
pytest -v           # Verbose
```

## 🔍 Code Quality

```bash
mypy src/           # Type checking
ruff check src/     # Linting
ruff format src/    # Format
```

## 📦 Dependencies

- FastAPI 0.104.1
- Pydantic 2.5.0
- Pytest 7.4.3
- SQLAlchemy 2.0.23
- PostgreSQL support

## 🔐 Security Features

- ✅ Typed errors (no raw exceptions)
- ✅ Pydantic validation
- ✅ CORS middleware
- ✅ Environment-based secrets
- ✅ Non-root Docker container
- ✅ Health checks

## 📄 Configuration

Configuration via environment variables (see `.env.example`):
- `APP_NAME` - Application name
- `DEBUG` - Debug mode
- `LOG_LEVEL` - Logging level
- `DATABASE_URL` - Database connection
- `API_PORT` - Server port
- `JWT_SECRET_KEY` - JWT secret

## 🎯 Design Decisions

1. **Clean Architecture** - Separation of concerns (routes, services, repositories)
2. **Type Safety** - Full Python type hints with mypy
3. **Error Handling** - Typed error hierarchy, no raw exceptions
4. **Event-Driven** - Async event bus for cross-module communication
5. **Testing** - Integration tests with TestClient
6. **Documentation** - Self-documenting with Pydantic and FastAPI

## 📞 Support

Email: krishnaraj.jagannathanrajan@cognizant.com

---

**Built with FastAPI, Python 3.12, and clean architecture**
