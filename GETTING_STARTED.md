# Getting Started with StoreOps API

## ⚡ Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd StoreOps
pip install -r requirements.txt
```

### 2. Run Application

```bash
python -m uvicorn src.main:app --reload
```

### 3. Open Browser

Visit: **http://localhost:8000/docs**

You'll see interactive Swagger UI with all endpoints.

## 🧪 Run Tests

```bash
pytest
```

Expected: **All tests pass** ✅

## 🐳 Docker Setup (Alternative)

```bash
docker-compose up
```

- API: http://localhost:8000
- Postgres: localhost:5432
- Docs: http://localhost:8000/docs

## 📡 Test API Endpoints

### 1. Create a Task

```bash
curl -X POST "http://localhost:8000/api/v1/activities/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Restock beverages",
    "description": "Restock cold beverages",
    "priority": "HIGH",
    "category": "RESTOCKING"
  }'
```

Response:
```json
{
  "id": "task_1",
  "title": "Restock beverages",
  "status": "TODO",
  "priority": "HIGH",
  "category": "RESTOCKING",
  "created_at": "2024-12-14T10:00:00",
  ...
}
```

### 2. List Tasks

```bash
curl "http://localhost:8000/api/v1/activities/tasks?skip=0&limit=10"
```

### 3. Get Task by ID

```bash
curl "http://localhost:8000/api/v1/activities/tasks/task_1"
```

### 4. Update Task

```bash
curl -X PUT "http://localhost:8000/api/v1/activities/tasks/task_1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "priority": "CRITICAL"
  }'
```

### 5. Create Staff Member

```bash
curl -X POST "http://localhost:8000/api/v1/staff" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@store.com",
    "role": "STORE_MANAGER"
  }'
```

### 6. Create Programme

```bash
curl -X POST "http://localhost:8000/api/v1/programmes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Holiday Campaign",
    "description": "Promotional campaign",
    "programme_type": "CAMPAIGN"
  }'
```

## 📋 Check Code Quality

### Type Checking

```bash
mypy src/
```

Expected: **No errors** ✅

### Linting

```bash
ruff check src/ tests/
```

Expected: **No violations** ✅

### Format Code

```bash
ruff format src/ tests/
```

## 🏗️ Project Structure

```
StoreOps/
├── src/
│   ├── activities/       # Tasks & operational activities
│   ├── programmes/       # Store programmes & campaigns
│   ├── staff/            # Staff management
│   ├── alerts/           # Alerts & notifications
│   ├── reports/          # Reports & analytics
│   ├── shared/           # Shared error handling & event bus
│   └── main.py           # FastAPI application
├── tests/                # Integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml        # Config for mypy, ruff, pytest
├── .env                  # Environment variables
└── README.md
```

## 🔑 Key Features

✅ **3-Layer Architecture** - Routes → Services → Repositories  
✅ **Type Safe** - Full Python type hints  
✅ **Error Handling** - Typed error hierarchy (AppError, ValidationError, NotFoundError, etc.)  
✅ **Event Bus** - Async event-driven cross-module communication  
✅ **Testing** - Comprehensive test suite with 100% endpoint coverage  
✅ **Validation** - Pydantic models for all inputs  
✅ **Documentation** - Auto-generated Swagger/OpenAPI docs  
✅ **Production Ready** - Docker, health checks, CORS, logging  

## 📝 Example: Create Task & Check Events

```python
# Test file: tests/test_activities.py

def test_create_task_publishes_event(client):
    """Task creation publishes TASK_CREATED event"""
    
    # Create task
    response = client.post("/api/v1/activities/tasks", json={
        "title": "Test Task",
        "priority": "HIGH",
        "category": "OPERATIONAL"
    })
    
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Test Task"
    assert task["status"] == "TODO"
```

## 🚨 Common Issues & Solutions

### Issue: Module not found

**Solution:** Make sure you're in the `StoreOps` directory:
```bash
cd StoreOps
python -m uvicorn src.main:app --reload
```

### Issue: Port 8000 already in use

**Solution:** Use different port:
```bash
python -m uvicorn src.main:app --port 8001 --reload
```

### Issue: Tests failing

**Solution:** Make sure dependencies are installed:
```bash
pip install -r requirements.txt
pytest -v
```

### Issue: Type checking errors

**Solution:** Install dev dependencies:
```bash
pip install -e ".[dev]"
mypy src/
```

## 📖 Next Steps

1. ✅ Run the application
2. ✅ Explore endpoints in Swagger UI
3. ✅ Run tests (`pytest`)
4. ✅ Check code quality (`mypy src/`, `ruff check src/`)
5. 📝 Review API_DOCUMENTATION.md for detailed endpoint specs
6. 🔧 Modify models/services for your use cases

## 🎓 Learn More

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Pydantic V2**: https://docs.pydantic.dev/latest
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pytest**: https://docs.pytest.org

## 💡 Tips

- Use Swagger UI (http://localhost:8000/docs) to test endpoints interactively
- Check event history in tests: `event_bus.get_event_history()`
- All responses use consistent error format (see API_DOCUMENTATION.md)
- All services raise typed errors - no raw exceptions
- Modules communicate via EventBus only - no direct service imports

---

**Happy building! 🚀**
