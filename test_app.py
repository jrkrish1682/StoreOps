"""Quick test to verify the application works"""

import sys

try:
    print("Testing StoreOps API Application...")
    print()

    # Test imports
    print("1. Testing imports...")
    from src.main import app
    from src.shared.errors import AppError
    from src.shared.event_bus import get_event_bus
    print("   ✅ All modules imported successfully")
    print()

    # Test FastAPI app
    print("2. Testing FastAPI app...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    print("   ✅ TestClient created successfully")
    print()

    # Test health endpoint
    print("3. Testing health check...")
    response = client.get("/health")
    assert response.status_code == 200
    print(f"   ✅ Health check: {response.status_code}")
    print(f"   ✅ Response: {response.json()}")
    print()

    # Test API root
    print("4. Testing API root...")
    response = client.get("/api/v1")
    assert response.status_code == 200
    modules = list(response.json()["modules"].keys())
    print(f"   ✅ API modules: {modules}")
    print()

    # Test Activities endpoint
    print("5. Testing Activities endpoints...")
    # Create task
    task_data = {
        "title": "Test Task",
        "priority": "HIGH",
        "category": "OPERATIONAL"
    }
    response = client.post("/api/v1/activities/tasks", json=task_data)
    assert response.status_code == 201
    task = response.json()
    task_id = task["id"]
    print(f"   ✅ Create task: {response.status_code}")
    print(f"   ✅ Task ID: {task_id}")

    # Get task
    response = client.get(f"/api/v1/activities/tasks/{task_id}")
    assert response.status_code == 200
    print(f"   ✅ Get task: {response.status_code}")
    print()

    # Test Programmes endpoint
    print("6. Testing Programmes endpoints...")
    prog_data = {
        "name": "Test Programme",
        "programme_type": "CAMPAIGN"
    }
    response = client.post("/api/v1/programmes", json=prog_data)
    assert response.status_code == 201
    print(f"   ✅ Create programme: {response.status_code}")
    print()

    # Test Staff endpoint
    print("7. Testing Staff endpoints...")
    staff_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
        "role": "STORE_MANAGER"
    }
    response = client.post("/api/v1/staff", json=staff_data)
    assert response.status_code == 201
    print(f"   ✅ Create staff: {response.status_code}")
    print()

    # Test Alerts endpoint
    print("8. Testing Alerts endpoints...")
    alert_data = {
        "title": "Test Alert",
        "alert_type": "SLA_BREACH",
        "severity": "HIGH"
    }
    response = client.post("/api/v1/alerts", json=alert_data)
    assert response.status_code == 201
    print(f"   ✅ Create alert: {response.status_code}")
    print()

    # Test Reports endpoint
    print("9. Testing Reports endpoints...")
    report_data = {
        "title": "Test Report",
        "report_type": "STORE_SUMMARY"
    }
    response = client.post("/api/v1/reports", json=report_data)
    assert response.status_code == 201
    print(f"   ✅ Create report: {response.status_code}")
    print()

    # Test error handling
    print("10. Testing error handling...")
    response = client.get("/api/v1/activities/tasks/nonexistent")
    assert response.status_code == 404
    error = response.json()
    print(f"   ✅ 404 error handling: {response.status_code}")
    if "error_code" in error:
        print(f"   ✅ Error code: {error['error_code']}")
    else:
        print(f"   ✅ Error response: {error}")
    print()

    print("=" * 60)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run: python -m uvicorn src.main:app --reload")
    print("2. Open: http://localhost:8000/docs")
    print("3. Run tests: pytest")
    print()

except AssertionError as e:
    print(f"❌ Assertion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
