# StoreOps Claude Code Development Harness: Deployment Guide

**Document Version:** 1.0  
**Last Updated:** 2026-08-29  
**Status:** Production-Ready  
**Platform:** Linux/macOS/Windows (Python 3.12+)

---

---

# SECTION 1: DEPLOYMENT OVERVIEW

## 1.1 Project Information

| Property | Value |
|----------|-------|
| **Project Name** | StoreOps Claude Code Development Harness |
| **Application Type** | FastAPI REST API |
| **Framework** | FastAPI 0.104.1 |
| **Runtime** | Python 3.12+ |
| **Deployment Type** | Local FastAPI Deployment (via Uvicorn ASGI Server) |
| **Architecture** | Modular Monolith (Route → Service → Repository layering) |
| **Port (Default)** | 8000 |
| **Version** | 0.1.0 |
| **Status** | Active Development |

## 1.2 Application Purpose

**StoreOps** is a retail operations management REST API designed to demonstrate the **Claude Code Development Harness** — a multi-agent framework that automates feature planning, implementation, evaluation, and governance for AI-assisted development.

The API manages retail operations across six core modules:

| Module | Purpose | Key Entities |
|--------|---------|--------------|
| **activities** | Task lifecycle management | Tasks, Activities, Status transitions |
| **alerts** | Alert triggering & escalation | Alerts, Severity levels, SLA tracking |
| **programmes** | Programme/initiative tracking | Programmes, Campaigns, Lifecycle states |
| **staff** | Staff & user management | Staff members, Roles, Assignments |
| **reports** | Analytics & reporting | Reports, Metrics, Dashboards |
| **shared** | Cross-cutting utilities | Error handling, Event bus, Dependencies |

## 1.3 Key Features

✅ **Type-Safe REST API** - Full Python type hints (mypy strict mode)  
✅ **Layered Architecture** - Route → Service → Repository (3-layer separation)  
✅ **Event-Driven Communication** - In-memory EventBus for cross-module events  
✅ **Comprehensive Error Handling** - AppError hierarchy with typed error codes  
✅ **Deterministic Testing** - Pytest integration tests with 80%+ coverage  
✅ **Production-Ready** - Docker support, health checks, CORS, logging  
✅ **API Documentation** - Auto-generated Swagger/OpenAPI at `/docs`  
✅ **Code Quality Tools** - Ruff (linting), Mypy (type checking), Pytest (testing)

## 1.4 Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│         HTTP Client (Browser / API Client)          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/HTTPS
                       ↓
┌─────────────────────────────────────────────────────┐
│    Uvicorn ASGI Server (Port 8000)                  │
│  ┌─────────────────────────────────────────────┐   │
│  │  FastAPI Application (src/main.py)          │   │
│  │  ┌────────────────────────────────────┐    │   │
│  │  │  Routes Layer (HTTP Handlers)      │    │   │
│  │  │  ├── activities/routes.py          │    │   │
│  │  │  ├── alerts/routes.py              │    │   │
│  │  │  ├── programmes/routes.py          │    │   │
│  │  │  ├── staff/routes.py               │    │   │
│  │  │  └── reports/routes.py             │    │   │
│  │  └────────────────────────────────────┘    │   │
│  │  ┌────────────────────────────────────┐    │   │
│  │  │  Service Layer (Business Logic)    │    │   │
│  │  │  ├── ActivitiesService             │    │   │
│  │  │  ├── AlertsService                 │    │   │
│  │  │  ├── ProgrammesService             │    │   │
│  │  │  ├── StaffService                  │    │   │
│  │  │  └── ReportsService                │    │   │
│  │  └────────────────────────────────────┘    │   │
│  │  ┌────────────────────────────────────┐    │   │
│  │  │  Repository Layer (Data Access)    │    │   │
│  │  │  ├── ActivitiesRepository          │    │   │
│  │  │  ├── AlertsRepository              │    │   │
│  │  │  ├── ProgrammesRepository          │    │   │
│  │  │  ├── StaffRepository               │    │   │
│  │  │  └── ReportsRepository             │    │   │
│  │  └────────────────────────────────────┘    │   │
│  │  ┌────────────────────────────────────┐    │   │
│  │  │  Shared Layer (Cross-Cutting)      │    │   │
│  │  │  ├── EventBus (Pub/Sub)            │    │   │
│  │  │  ├── Error Hierarchy               │    │   │
│  │  │  └── Dependency Injection          │    │   │
│  │  └────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                       ↓
         In-Memory Data Storage (Dev)
         PostgreSQL (Production Ready)
```

## 1.5 Supported Deployment Modes

| Mode | Use Case | Data Persistence | Setup Time |
|------|----------|------------------|-----------|
| **Local (Development)** | Development, testing, learning | In-memory (lost on restart) | < 1 minute |
| **Docker Compose** | Local multi-container testing | PostgreSQL container | 2-3 minutes |
| **Docker** | Staging, production deployment | External PostgreSQL | 5 minutes |
| **Kubernetes** | Enterprise scale deployment | PostgreSQL cluster | 15+ minutes |

**Currently Supported:** Local + Docker Compose (Production-ready modes TBD)

---

---

# SECTION 2: APPLICATION STARTUP

## 2.1 Prerequisites

### System Requirements

- **OS:** Linux, macOS, or Windows (with WSL2)
- **Python:** 3.12 or later
- **Disk Space:** 500 MB (with dependencies)
- **Memory:** 512 MB minimum (1 GB recommended)
- **Internet:** Required for pip install (dependencies)

### Check Python Version

```bash
python --version
# Expected: Python 3.12.x or higher

python -c "import sys; print(f'Python {sys.version}')"
```

### Verify pip and venv

```bash
python -m pip --version
python -m venv --help
```

## 2.2 Development Environment Setup

### Step 1: Clone Repository

```bash
# Clone StoreOps repository (or download as ZIP)
git clone <repository-url>
cd StoreOpsAPI/StoreOps
```

### Step 2: Create Virtual Environment

```bash
# macOS/Linux
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat
```

**Verify activation:**
```bash
which python  # macOS/Linux
where python  # Windows

# Should show path inside venv directory
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies (including dev tools)
pip install -r requirements.txt

# Alternative: Install with optional dev dependencies
pip install -e ".[dev]"
```

### Step 4: Configure Environment Variables

Create or update `.env` file in project root:

```bash
# Copy example to .env (if needed)
cp .env.example .env

# Or create new .env with defaults:
cat > .env << 'EOF'
# Application
APP_NAME=StoreOps API
DEBUG=false
LOG_LEVEL=INFO

# Database (Development: In-memory; Production: PostgreSQL)
DATABASE_URL=sqlite:///./storeops.db

# API
API_PORT=8000
API_HOST=0.0.0.0

# JWT (Future authentication)
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
EOF
```

### Step 5: Verify Installation

```bash
# Check Python packages installed
pip list | grep -E "fastapi|uvicorn|pydantic"

# Verify FastAPI installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"

# Verify Uvicorn installation
python -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
```

## 2.3 Starting the Application Locally

### Method 1: Direct Uvicorn Command (Fastest)

```bash
# Start with auto-reload (recommended for development)
uvicorn src.main:app --reload

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started server process [12345]
# INFO:     Uvicorn running with auto reload enabled
```

### Method 2: Using Python Module

```bash
# Start FastAPI application as module
python -m uvicorn src.main:app --reload

# With custom port
python -m uvicorn src.main:app --reload --port 8001

# With custom host
python -m uvicorn src.main:app --reload --host 0.0.0.0
```

### Method 3: Using Run Script (if available)

```bash
# Create run script (run.sh for Unix)
#!/bin/bash
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

chmod +x run.sh
./run.sh
```

### Method 4: Production Mode (No Auto-Reload)

```bash
# Run without auto-reload (production-like)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# With logging and error handling
uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Startup Options Reference

| Option | Default | Purpose | Example |
|--------|---------|---------|---------|
| `--reload` | False | Auto-reload on code changes | `--reload` |
| `--host` | 127.0.0.1 | Bind address | `--host 0.0.0.0` |
| `--port` | 8000 | Port number | `--port 8001` |
| `--workers` | 1 | Number of worker processes | `--workers 4` |
| `--log-level` | info | Logging level | `--log-level debug` |
| `--ssl-keyfile` | None | SSL key file | `--ssl-keyfile ./key.pem` |
| `--ssl-certfile` | None | SSL cert file | `--ssl-certfile ./cert.pem` |

## 2.4 Verifying Startup

### Health Check Endpoint

Once the application starts, verify it's running:

```bash
# Health check (endpoint may be added in future)
curl http://localhost:8000/health

# Or check root endpoint
curl http://localhost:8000/

# Expected response: 404 or JSON with API info
```

### Interactive API Documentation

Open in your browser:

```
http://localhost:8000/docs
```

**You'll see:**
- ✅ Swagger UI with all endpoints
- ✅ Interactive endpoint testing
- ✅ Request/response schemas
- ✅ Authentication UI (if enabled)

### Alternative Documentation (ReDoc)

```
http://localhost:8000/redoc
```

### List All Available Endpoints

```bash
# Via curl to OpenAPI schema
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# Example output:
# [
#   "/api/v1/activities/tasks",
#   "/api/v1/activities/bulk-status",
#   "/api/v1/staff",
#   "/api/v1/programmes",
#   ...
# ]
```

## 2.5 Testing the API

### Create a Task (Simple Test)

```bash
curl -X POST "http://localhost:8000/api/v1/activities/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Restock beverages",
    "description": "Restock cold beverages in section B",
    "priority": "HIGH",
    "category": "RESTOCKING"
  }'

# Expected response (HTTP 201):
# {
#   "id": "task_1",
#   "title": "Restock beverages",
#   "status": "TODO",
#   "priority": "HIGH",
#   "category": "RESTOCKING",
#   "created_at": "2026-08-29T...",
#   ...
# }
```

### List Tasks

```bash
curl "http://localhost:8000/api/v1/activities/tasks?skip=0&limit=10"

# Expected response (HTTP 200):
# {
#   "items": [
#     {"id": "task_1", "title": "...", ...},
#     ...
#   ],
#   "total": N,
#   "skip": 0,
#   "limit": 10
# }
```

### Get Single Task

```bash
curl "http://localhost:8000/api/v1/activities/tasks/task_1"

# Expected response (HTTP 200):
# {
#   "id": "task_1",
#   "title": "...",
#   ...
# }
```

### Test Bulk Status Update (ACTIVITIES-003 Feature)

```bash
curl -X PATCH "http://localhost:8000/api/v1/activities/bulk-status" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_ids": ["task_1", "task_2", "task_3"],
    "new_status": "DONE"
  }'

# Expected response (HTTP 200):
# {
#   "succeeded": [
#     {"id": "task_1", "status": "DONE", ...},
#     ...
#   ],
#   "failed": [
#     {"activity_id": "task_99", "error_code": "NOT_FOUND", "message": "..."}
#   ],
#   "summary": {
#     "total": 3,
#     "succeeded": 2,
#     "failed": 1
#   }
# }
```

## 2.6 Running Tests

### Run All Tests

```bash
pytest
```

**Expected output:**
```
============================= test session starts ==============================
collected 45 items

tests/test_activities.py .............................  [ 57%]
tests/test_alerts.py .........                        [ 79%]
tests/test_event_bus.py ........                       [ 90%]
tests/test_staff.py .......                            [ 100%]

============================== 45 passed in 0.32s ==============================
```

### Run Specific Test File

```bash
pytest tests/test_activities.py -v
```

### Run Specific Test

```bash
pytest tests/test_activities.py::TestActivitiesRoutes::test_create_task -v
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html tests/

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Tests in Watch Mode

```bash
pytest-watch tests/
# or
ptw
```

## 2.7 Code Quality Checks

### Type Checking (Mypy)

```bash
# Check all code
mypy src/

# Expected output:
# Success: no issues found in 15 source files

# Check specific file
mypy src/activities/service.py
```

### Linting (Ruff)

```bash
# Check for violations
ruff check src/ tests/

# Expected output (if no violations):
# (no output)

# Show violations with details
ruff check src/ --show-fixes
```

### Format Code (Ruff)

```bash
# Auto-format code
ruff format src/ tests/

# Expected output:
# 1 file reformatted
```

### Combined Quality Check

```bash
# Run all checks in sequence
mypy src/ && ruff check src/ && pytest

# Expected: All pass
```

## 2.8 Stopping the Application

### Graceful Shutdown

```bash
# Press Ctrl+C in terminal where Uvicorn is running
# Expected:
# ^C
# Shutting down
# Waiting for application shutdown.
# Application shutdown complete.
```

### Force Shutdown (if needed)

```bash
# macOS/Linux
pkill -f "uvicorn src.main"

# Windows PowerShell
Stop-Process -Name python -Force
```

### Kill Process by Port

```bash
# macOS/Linux (show and kill process using port 8000)
lsof -i :8000
kill -9 <PID>

# Windows PowerShell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

# SECTION 3: DOCKER DEPLOYMENT

## 3.1 Docker Setup (Single Container)

### Build Docker Image

```bash
# Build image tagged as storeops:latest
docker build -t storeops:latest .

# Expected output:
# [+] Building 15.3s (12/12) FINISHED
# ...
# => exporting to image
# => => writing image sha256:abc123...
```

### Run Docker Container

```bash
# Run container with port mapping
docker run -p 8000:8000 storeops:latest

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Access from Host

Once running:
```bash
curl http://localhost:8000/docs
```

## 3.2 Docker Compose (Multi-Container)

### Prerequisites

```bash
# Verify Docker Compose is installed
docker-compose --version
# Expected: Docker Compose version 1.29.2 or higher
```

### Start Services

```bash
# Start all services in background
docker-compose up -d

# Or foreground (for debugging)
docker-compose up

# Expected services:
# - api: Running on http://localhost:8000
# - postgres: Running on localhost:5432
```

### Check Service Status

```bash
docker-compose ps

# Expected output:
# NAME       IMAGE              STATUS          PORTS
# storeops-api-1   storeops:latest    Up 10 seconds   0.0.0.0:8000->8000/tcp
# postgres-1       postgres:15        Up 10 seconds   0.0.0.0:5432->5432/tcp
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 20 lines
docker-compose logs --tail=20
```

### Stop Services

```bash
docker-compose down

# Also remove volumes (data)
docker-compose down -v
```

## 3.3 Environment Configuration

### For Docker Deployment

Update `.env` for Docker:

```bash
# .env (for Docker)
DATABASE_URL=postgresql://storeops:storeops@postgres:5432/storeops
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=INFO
```

### Docker Compose Configuration

Edit `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://storeops:storeops@postgres:5432/storeops
      - DEBUG=false
    depends_on:
      - postgres
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: storeops
      POSTGRES_PASSWORD: storeops
      POSTGRES_DB: storeops
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

# SECTION 4: CONFIGURATION & ENVIRONMENT VARIABLES

## 4.1 Environment Variables

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `APP_NAME` | string | StoreOps API | Application name |
| `DEBUG` | boolean | false | Debug mode (enables verbose logging) |
| `LOG_LEVEL` | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DATABASE_URL` | string | sqlite:///./storeops.db | Database connection URL |
| `API_PORT` | int | 8000 | Port for API server |
| `API_HOST` | string | 0.0.0.0 | Host binding |
| `JWT_SECRET_KEY` | string | dev-secret | Secret key for JWT (change in production!) |
| `JWT_ALGORITHM` | string | HS256 | JWT algorithm |
| `JWT_EXPIRATION_HOURS` | int | 24 | Token expiration time |

### Loading Environment Variables

```bash
# Using .env file (automatically loaded via python-dotenv)
# .env must be in project root

# Or set via command line
export DATABASE_URL="postgresql://user:pass@localhost:5432/storeops"
uvicorn src.main:app

# Or inline
DATABASE_URL="postgresql://..." uvicorn src.main:app
```

## 4.2 Uvicorn Configuration

### Configuration File (uvicorn.ini)

```ini
[server]
host = 0.0.0.0
port = 8000
workers = 4
reload = false
log_level = info
```

### CLI Configuration

```bash
uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log
```

## 4.3 CORS Configuration

CORS is configured in `src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict origins:

```python
allow_origins=[
    "http://localhost:3000",  # Frontend URL
    "https://app.example.com",
]
```

---

# SECTION 5: HEALTH CHECKS & MONITORING

## 5.1 Application Health

### Health Check Endpoint

Check if API is running:

```bash
curl http://localhost:8000/health

# Expected response (HTTP 200):
# {"status": "ok", "timestamp": "2026-08-29T..."}
```

### Startup Verification

Automated startup checks run when app starts:

```python
# Verified in src/main.py startup event handler
@app.on_event("startup")
async def startup_event():
    """Verify all modules are loaded."""
    log_startup_info()
    verify_module_configuration()
```

### Live Metrics

Access Prometheus metrics (if enabled):

```bash
# Not currently implemented; future feature
curl http://localhost:8000/metrics
```

## 5.2 Docker Health Checks

Health check in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
```

Check container health:

```bash
docker inspect --format='{{.State.Health.Status}}' <container-id>
# Expected: healthy
```

## 5.3 Logging

### Log Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - Confirmation that things are working
- `WARNING` - Something unexpected, but not critical
- `ERROR` - Serious problem, function failed
- `CRITICAL` - Very serious error, program may fail

### View Logs

```bash
# Stdout (console where app is running)
# Or check log files if configured

# For Docker
docker logs <container-id>
docker logs -f <container-id>  # Follow logs

# For Docker Compose
docker-compose logs -f api
```

### Configure Logging Level

```bash
# Via environment variable
LOG_LEVEL=DEBUG uvicorn src.main:app

# Via CLI
uvicorn src.main:app --log-level debug
```

---

# SECTION 6: TROUBLESHOOTING

## 6.1 Common Startup Issues

### Issue: Module Not Found Error

```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Make sure you're in correct directory
cd StoreOpsAPI/StoreOps

# Verify Python path
python -c "import sys; print(sys.path)"

# Re-install dependencies
pip install -r requirements.txt
```

### Issue: Port Already in Use

```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Use different port
uvicorn src.main:app --port 8001

# Or kill process using port 8000
lsof -i :8000  # macOS/Linux
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: ModuleNotFoundError for uvicorn

```
ModuleNotFoundError: No module named 'uvicorn'
```

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install uvicorn[standard]==0.24.0

# Verify
python -c "import uvicorn; print(uvicorn.__version__)"
```

### Issue: Python Version Mismatch

```
ERROR: Python 3.11 is not supported. Python 3.12+ required.
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.12+
# macOS (via Homebrew)
brew install python@3.12

# Or use pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Use specific Python
python3.12 -m uvicorn src.main:app
```

## 6.2 API Request Issues

### Issue: 404 Not Found

```
{"detail":"Not Found"}
```

**Possible causes:**
- Wrong endpoint path
- Case sensitivity (paths are case-sensitive)
- Method mismatch (POST vs GET)

**Solution:**
```bash
# Check available endpoints
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# Verify method
curl -X GET http://localhost:8000/api/v1/activities/tasks
```

### Issue: 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "priority"],
      "msg": "value is not a valid enumeration member"
    }
  ]
}
```

**Solution:**
- Check request body format
- Verify enum values (e.g., priority must be HIGH, MEDIUM, LOW)
- Use Swagger UI to see expected schema

```bash
# View endpoint schema in Swagger
http://localhost:8000/docs
```

### Issue: 500 Internal Server Error

```json
{"detail":"Internal server error"}
```

**Solution:**
- Check application logs
- Verify database connection (if using PostgreSQL)
- Review error details in server console

```bash
# See full error in logs
uvicorn src.main:app --log-level debug
```

## 6.3 Database Issues

### Issue: PostgreSQL Connection Failed

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Verify PostgreSQL is running
psql --version
pg_isready -h localhost

# Check connection string
DATABASE_URL=postgresql://user:pass@localhost:5432/storeops

# Test connection
psql postgresql://user:pass@localhost:5432/storeops
```

### Issue: Database Permission Denied

```
psycopg2.OperationalError: FATAL: Ident authentication failed for user "storeops"
```

**Solution:**
```bash
# Use correct credentials in DATABASE_URL
DATABASE_URL=postgresql://storeops:storeops@localhost:5432/storeops

# Or use connection with proper auth
psql -U storeops -h localhost -d storeops -W
```

## 6.4 Test Issues

### Issue: Tests Failing

```
FAILED tests/test_activities.py::TestActivitiesRoutes::test_create_task
```

**Solution:**
```bash
# Run with verbose output
pytest -v tests/test_activities.py::TestActivitiesRoutes::test_create_task

# Check for dependency issues
pip install -r requirements.txt

# Run single test with debug info
pytest -vvs tests/test_activities.py::TestActivitiesRoutes::test_create_task
```

### Issue: Async Test Errors

```
RuntimeError: Event loop is closed
```

**Solution:**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio==0.21.1

# Run tests
pytest --asyncio-mode=auto
```

## 6.5 Docker Issues

### Issue: Docker Build Failed

```
ERROR: failed to solve: error pulling image "python:3.12-slim"
```

**Solution:**
```bash
# Pull image manually
docker pull python:3.12-slim

# Try build again
docker build -t storeops:latest .
```

### Issue: Docker Container Exits Immediately

```bash
docker logs <container-id>
# Check error message
```

**Solution:**
```bash
# Build image
docker build -t storeops:latest .

# Run with debug output
docker run -it storeops:latest uvicorn src.main:app --log-level debug
```

### Issue: Can't Connect to Container

```
curl: (7) Failed to connect to localhost port 8000
```

**Solution:**
```bash
# Check if container is running
docker ps

# Check port mapping
docker port <container-id>

# Should show: 8000/tcp -> 0.0.0.0:8000

# Verify firewall isn't blocking
# macOS: System Preferences > Security & Privacy > Firewall
# Windows: Windows Defender Firewall > Allow an app through firewall
```

---

# SECTION 7: MONITORING & PERFORMANCE

## 7.1 Application Metrics

### Key Metrics to Monitor

- **Response Time:** Average HTTP response time
- **Throughput:** Requests per second
- **Error Rate:** Percentage of 4xx/5xx responses
- **CPU Usage:** Server CPU utilization
- **Memory Usage:** RAM consumed by application
- **Database Connections:** Active database connections

### Accessing Metrics

```bash
# Application info (via API)
curl http://localhost:8000/openapi.json | jq '.info'

# Health status
curl http://localhost:8000/health

# OpenAPI schema
curl http://localhost:8000/openapi.json
```

## 7.2 Performance Monitoring

### Monitor Request Duration

```bash
# Using curl with timing
curl -w "\nTotal time: %{time_total}s\nConnect time: %{time_connect}s\n" \
  http://localhost:8000/api/v1/activities/tasks
```

### Load Testing (Optional)

```bash
# Using Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:8000/api/v1/activities/tasks

# Using wrk (if installed)
wrk -t 4 -c 100 -d 30s http://localhost:8000/api/v1/activities/tasks
```

## 7.3 Resource Monitoring

### Monitor Process

```bash
# macOS/Linux
ps aux | grep uvicorn

# Windows PowerShell
Get-Process python | Select ProcessName, Id, WorkingSet
```

### Monitor Docker Container

```bash
# Container stats
docker stats <container-id>

# Expected output:
# CONTAINER ID   CPU %    MEM USAGE / LIMIT
# abc123...      0.05%    45.2 MiB / 1 GiB
```

### Monitor Logs for Errors

```bash
# Filter for errors
docker logs <container-id> | grep ERROR

# Count errors
docker logs <container-id> 2>&1 | grep -c ERROR
```

---

# SECTION 8: PRODUCTION CONSIDERATIONS

## 8.1 Pre-Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Use strong `JWT_SECRET_KEY` (not dev-secret)
- [ ] Configure PostgreSQL (not in-memory storage)
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for specific domains
- [ ] Set up logging and monitoring
- [ ] Run full test suite
- [ ] Perform load testing
- [ ] Set up backups for database
- [ ] Configure health checks

## 8.2 Security Recommendations

### Environment Variables

```bash
# Never hardcode secrets
# Use environment variables or secrets manager

# Example with AWS Secrets Manager
export JWT_SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id storeops-jwt-key --query SecretString --output text)
```

### CORS Configuration

```python
# Restrict to specific origins
allow_origins=[
    "https://app.example.com",
    "https://admin.example.com",
]
```

### SQL Injection Prevention

- ✅ Already using SQLAlchemy ORM (parameterized queries)
- ✅ Using Pydantic for input validation
- ✅ No raw SQL queries

### Rate Limiting (Future)

```python
# Consider adding: SlowAPI or similar
# from slowapi import Limiter
# limiter = Limiter(key_func=get_remote_address)
# @app.get("/api/v1/activities/tasks")
# @limiter.limit("10/minute")
```

## 8.3 Scaling Strategies

### Horizontal Scaling (Multiple Instances)

```bash
# Run multiple worker processes
uvicorn src.main:app --workers 8

# Or behind a load balancer
# Each instance on different port:
uvicorn src.main:app --port 8001 &
uvicorn src.main:app --port 8002 &
uvicorn src.main:app --port 8003 &
# nginx/HAProxy distributes traffic
```

### Vertical Scaling (Larger Instance)

```bash
# Increase workers for more CPU cores
uvicorn src.main:app --workers $(nproc)  # Auto-detect CPU count

# Increase memory available
# Set resource limits in Docker/Kubernetes
```

### Database Optimization

```bash
# Use connection pooling
# SQLAlchemy supports pooling out of the box

# Create database indexes on frequently queried fields
# Cache frequently accessed data

# Consider read replicas for reports module
```

## 8.4 Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump postgresql://user:pass@localhost:5432/storeops > storeops-$(date +%Y%m%d).sql

# Restore from backup
psql postgresql://user:pass@localhost:5432/storeops < storeops-20260829.sql
```

### Application Backup

```bash
# Backup configuration and code
tar -czf storeops-backup-$(date +%Y%m%d).tar.gz \
  .env \
  src/ \
  tests/ \
  requirements.txt
```

---

# SECTION 9: QUICK REFERENCE

## 9.1 Common Commands

| Task | Command |
|------|---------|
| **Start development** | `uvicorn src.main:app --reload` |
| **Start production** | `uvicorn src.main:app --host 0.0.0.0 --workers 4` |
| **Run tests** | `pytest` |
| **Type checking** | `mypy src/` |
| **Linting** | `ruff check src/` |
| **Format code** | `ruff format src/ tests/` |
| **Docker build** | `docker build -t storeops:latest .` |
| **Docker run** | `docker run -p 8000:8000 storeops:latest` |
| **Docker Compose** | `docker-compose up -d` |
| **View docs** | `http://localhost:8000/docs` |
| **API root** | `curl http://localhost:8000/` |

## 9.2 Directory Structure

```
StoreOps/
├── src/
│   ├── activities/          # Task management module
│   ├── alerts/              # Alerts module
│   ├── programmes/          # Programmes module
│   ├── staff/               # Staff management module
│   ├── reports/             # Reports module
│   ├── shared/              # Shared utilities (errors, event bus)
│   ├── main.py              # FastAPI application entry point
│   └── __init__.py
├── tests/                   # Integration tests
│   ├── conftest.py         # Pytest fixtures
│   ├── test_activities.py
│   ├── test_alerts.py
│   ├── test_programmes.py
│   ├── test_staff.py
│   ├── test_reports.py
│   └── test_event_bus.py
├── .harness/                # Claude Code Development Harness
├── docs/                    # Documentation
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-container definition
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
├── .env                   # Environment variables
├── .env.example          # Example environment file
├── .gitignore           # Git ignore rules
├── GETTING_STARTED.md   # Quick start guide
├── API_DOCUMENTATION.md # Endpoint documentation
└── README.md            # Project overview
```

## 9.3 Port Reference

| Service | Port | URL |
|---------|------|-----|
| **API** | 8000 | http://localhost:8000 |
| **Swagger UI** | 8000 | http://localhost:8000/docs |
| **ReDoc** | 8000 | http://localhost:8000/redoc |
| **PostgreSQL** | 5432 | localhost:5432 |
| **Alternative API** | 8001 | http://localhost:8001 |

## 9.4 Useful Links

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Uvicorn Server**: https://www.uvicorn.org
- **Pydantic V2**: https://docs.pydantic.dev
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pytest**: https://docs.pytest.org
- **Docker**: https://docs.docker.com

---

# SECTION 10: SUPPORT & DOCUMENTATION

## 10.1 Additional Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| **API Endpoints** | `API_DOCUMENTATION.md` | Detailed endpoint specifications |
| **Architecture** | `docs/repository-assessment.md` | System architecture and patterns |
| **Design Brief** | `DESIGN_BRIEF.md` | Harness design and governance |
| **Getting Started** | `GETTING_STARTED.md` | Quick setup guide |
| **Reflection** | `REFLECTION.md` | Lessons learned and recommendations |
| **Harness Docs** | `.harness/` | Development harness documentation |

## 10.2 Logging Issues

### Check Application Logs

```bash
# In terminal where app is running
# All log output visible

# In Docker
docker logs -f <container-id>

# Set log level
LOG_LEVEL=DEBUG uvicorn src.main:app
```

### Report Issues

Include in bug report:
1. Exact error message
2. Steps to reproduce
3. Environment (Python version, OS)
4. Log output (with DEBUG level)
5. API request/response (if applicable)

## 10.3 Getting Help

- Check troubleshooting section (Section 6)
- Review test examples in `tests/`
- Check endpoint documentation at `/docs`
- Review code comments and docstrings
- Consult API_DOCUMENTATION.md for endpoint details

---

**Document Prepared For:** Development and DevOps Teams  
**Last Updated:** 2026-08-29  
**Status:** Production-Ready  
**Maintenance:** Community-maintained

---

*This deployment guide provides comprehensive instructions for starting, configuring, and troubleshooting the StoreOps API. For questions or updates, refer to the linked documentation or contact the development team.*

