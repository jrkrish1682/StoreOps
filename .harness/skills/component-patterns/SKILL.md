# StoreOps Component Patterns

**Version:** 1.0.0  
**Last Updated:** 2026-08-29  
**Scope:** Reusable implementation patterns for new features in StoreOps

---

## Purpose

This skill provides step-by-step implementation patterns for building new features in StoreOps. Each pattern shows:
- Files affected
- Dependency direction (Routes → Services → Repositories)
- Skeleton code to copy and modify

**Use this skill when:**
- Adding a new endpoint
- Implementing a new service method
- Adding repository operations
- Creating request/response models
- Implementing error handling
- Publishing events

---

## Pattern 1: Adding a New Endpoint

### When to Use

You need to add an HTTP endpoint that calls existing service methods.

### Skeleton: CREATE (POST)

**Files Affected:**
- `src/{module}/routes.py` - Add route handler
- `src/{module}/service.py` - Verify method exists
- `src/{module}/models.py` - Verify models exist

**Implementation Steps:**

1. **Define Models** (if needed)

```python
# src/{module}/models.py

class ItemCreate(ItemBase):
    """Request model for creating item."""
    pass

class Item(ItemBase):
    """Response model for item."""
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}
```

2. **Add Route Handler**

```python
# src/{module}/routes.py

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(
    prefix="/api/v1/{module}",
    tags=["{module}"],
)

@router.post(
    "/items",
    response_model=Item,
    status_code=201,
)
async def create_item(
    item_create: ItemCreate,
    service: MyService = Depends(get_my_service),
) -> Item:
    """Create new item.
    
    Args:
        item_create: Item creation data
        service: Service for business logic
    
    Returns:
        Created item
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        return await service.create_item(item_create=item_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

3. **Verify Service Method**

```python
# src/{module}/service.py - Should already exist

async def create_item(self, item_create: ItemCreate) -> Item:
    """Create item with validation."""
    # Validation
    if not item_create.name or not item_create.name.strip():
        raise ValidationError(message="Item name is required")
    
    # Persist
    item = await self.repository.create(item_create)
    
    # Publish event
    await self.event_bus.publish(
        EventType.ITEM_CREATED,
        {"item_id": item.id, "name": item.name},
    )
    
    return item
```

### Skeleton: READ (GET by ID)

```python
# src/{module}/routes.py

@router.get(
    "/items/{item_id}",
    response_model=Item,
)
async def get_item(
    item_id: str,
    service: MyService = Depends(get_my_service),
) -> Item:
    """Get item by ID.
    
    Args:
        item_id: Item ID
        service: Service
    
    Returns:
        Item
    
    Raises:
        HTTPException: If item not found
    """
    try:
        return await service.get_item(item_id=item_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Skeleton: LIST (GET with pagination)

```python
# src/{module}/routes.py

from fastapi import Query

@router.get(
    "/items",
    response_model=ItemList,
)
async def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: MyService = Depends(get_my_service),
) -> ItemList:
    """List items with pagination.
    
    Args:
        skip: Items to skip
        limit: Max items to return
        service: Service
    
    Returns:
        Paginated item list
    """
    result = await service.list_items(skip=skip, limit=limit)
    return ItemList(**result)
```

### Skeleton: UPDATE (PUT)

```python
# src/{module}/routes.py

@router.put(
    "/items/{item_id}",
    response_model=Item,
)
async def update_item(
    item_id: str,
    item_update: ItemUpdate,
    service: MyService = Depends(get_my_service),
) -> Item:
    """Update item.
    
    Args:
        item_id: Item ID
        item_update: Update data
        service: Service
    
    Returns:
        Updated item
    
    Raises:
        HTTPException: If item not found or validation fails
    """
    try:
        return await service.update_item(
            item_id=item_id,
            item_update=item_update,
        )
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Skeleton: DELETE

```python
# src/{module}/routes.py

@router.delete(
    "/items/{item_id}",
    status_code=204,
)
async def delete_item(
    item_id: str,
    service: MyService = Depends(get_my_service),
) -> None:
    """Delete item.
    
    Args:
        item_id: Item ID
        service: Service
    
    Raises:
        HTTPException: If item not found
    """
    try:
        await service.delete_item(item_id=item_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Dependency Direction

```
Route Handler
    ↓ (calls)
Service Method
    ↓ (calls)
Repository Method
```

---

## Pattern 2: Adding a Service Method

### When to Use

You need to implement business logic that routes will call.

### Skeleton: CREATE with Validation

```python
# src/{module}/service.py

async def create_item(
    self,
    item_create: ItemCreate,
    current_user_id: str | None = None,
) -> Item:
    """Create item with validation.
    
    Args:
        item_create: Creation data
        current_user_id: User performing action
    
    Returns:
        Created item
    
    Raises:
        ValidationError: If validation fails
        ConflictError: If duplicate
    """
    # 1. Validation
    if not item_create.name or not item_create.name.strip():
        raise ValidationError(message="Item name is required")
    
    # 2. Business rule: Check duplicates
    existing = await self.repository.get_by_name(item_create.name)
    if existing:
        raise ConflictError(
            resource_type="Item",
            message=f"Item with name '{item_create.name}' already exists",
        )
    
    # 3. Persistence
    item = await self.repository.create(
        item_create=item_create,
        created_by=current_user_id,
    )
    
    # 4. Cross-module side effects via EventBus
    await self.event_bus.publish(
        EventType.ITEM_CREATED,
        {
            "item_id": item.id,
            "name": item.name,
            "created_by": current_user_id,
        },
    )
    
    return item
```

### Skeleton: GET with Not-Found Check

```python
# src/{module}/service.py

async def get_item(self, item_id: str) -> Item:
    """Get item by ID.
    
    Args:
        item_id: Item ID
    
    Returns:
        Item
    
    Raises:
        NotFoundError: If not found
    """
    item = await self.repository.get_by_id(item_id)
    if not item:
        raise NotFoundError(resource_type="Item", resource_id=item_id)
    return item
```

### Skeleton: LIST with Pagination

```python
# src/{module}/service.py

async def list_items(
    self,
    skip: int = 0,
    limit: int = 10,
) -> dict:
    """List items with pagination.
    
    Args:
        skip: Items to skip
        limit: Max items to return
    
    Returns:
        Dict with items, total, skip, limit
    """
    items, total = await self.repository.list_all(skip=skip, limit=limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
```

### Skeleton: UPDATE with Validation

```python
# src/{module}/service.py

async def update_item(
    self,
    item_id: str,
    item_update: ItemUpdate,
) -> Item:
    """Update item with validation.
    
    Args:
        item_id: Item ID
        item_update: Update data
    
    Returns:
        Updated item
    
    Raises:
        NotFoundError: If not found
        ValidationError: If validation fails
        BusinessRuleViolationError: If business rule violated
    """
    # 1. Get existing
    existing = await self.repository.get_by_id(item_id)
    if not existing:
        raise NotFoundError(resource_type="Item", resource_id=item_id)
    
    # 2. Validate update
    if item_update.name is not None:
        if not item_update.name or not item_update.name.strip():
            raise ValidationError(message="Item name cannot be empty")
    
    # 3. Business rule checks
    # Example: Can't move to archived if has active sub-items
    if item_update.status == "ARCHIVED" and existing.active_count > 0:
        raise BusinessRuleViolationError(
            message="Cannot archive item with active sub-items",
            rule_name="CANNOT_ARCHIVE_ACTIVE_ITEMS",
        )
    
    # 4. Update
    updated = await self.repository.update(item_id, item_update)
    if not updated:
        raise NotFoundError(resource_type="Item", resource_id=item_id)
    
    # 5. Publish events if state changed
    if (
        item_update.status
        and item_update.status != existing.status
        and item_update.status == "COMPLETED"
    ):
        await self.event_bus.publish(
            EventType.ITEM_COMPLETED,
            {"item_id": item_id, "completed_at": updated.updated_at.isoformat()},
        )
    
    return updated
```

### Skeleton: DELETE

```python
# src/{module}/service.py

async def delete_item(self, item_id: str) -> bool:
    """Delete item.
    
    Args:
        item_id: Item ID
    
    Returns:
        True if deleted
    
    Raises:
        NotFoundError: If not found
        BusinessRuleViolationError: If can't delete
    """
    # 1. Get existing
    existing = await self.repository.get_by_id(item_id)
    if not existing:
        raise NotFoundError(resource_type="Item", resource_id=item_id)
    
    # 2. Business rule: Can't delete if referenced
    if existing.is_referenced:
        raise BusinessRuleViolationError(
            message="Cannot delete item with active references",
            rule_name="ITEM_HAS_REFERENCES",
        )
    
    # 3. Delete
    deleted = await self.repository.delete(item_id)
    if not deleted:
        raise NotFoundError(resource_type="Item", resource_id=item_id)
    
    # 4. Publish event
    await self.event_bus.publish(
        EventType.ITEM_DELETED,
        {"item_id": item_id},
    )
    
    return True
```

### Service Structure

```python
class MyService:
    def __init__(
        self,
        repository: MyRepository,
        event_bus: EventBus,
    ) -> None:
        self.repository = repository
        self.event_bus = event_bus
    
    # Public methods
    async def create_item(self, ...):
        pass
    
    async def get_item(self, ...):
        pass
    
    async def list_items(self, ...):
        pass
    
    async def update_item(self, ...):
        pass
    
    async def delete_item(self, ...):
        pass
    
    # Private helper methods (prefix with _)
    async def _validate_item_name(self, name: str) -> None:
        pass


# Factory at end of file
async def get_my_service() -> MyService:
    """Factory for service."""
    repository = get_my_repository()
    from src.shared.event_bus import get_event_bus
    event_bus = get_event_bus()
    return MyService(repository=repository, event_bus=event_bus)
```

---

## Pattern 3: Adding Repository Operations

### When to Use

You need to add CRUD or query operations at the data access layer.

### Skeleton: CREATE

```python
# src/{module}/repository.py

async def create(
    self,
    item_create: ItemCreate,
    created_by: str | None = None,
) -> Item:
    """Create new item.
    
    Args:
        item_create: Creation data
        created_by: User who created
    
    Returns:
        Created item
    """
    self._counter += 1
    item_id = f"item_{self._counter}"
    now = datetime.now(UTC)
    
    item_data = {
        "id": item_id,
        "name": item_create.name,
        "description": item_create.description,
        "status": item_create.status,
        "created_at": now,
        "updated_at": now,
        "created_by": created_by,
    }
    
    self._items[item_id] = item_data
    return Item.model_validate(item_data)
```

### Skeleton: GET

```python
# src/{module}/repository.py

async def get_by_id(self, item_id: str) -> Item | None:
    """Get item by ID.
    
    Args:
        item_id: Item ID
    
    Returns:
        Item or None
    """
    item_data = self._items.get(item_id)
    return Item.model_validate(item_data) if item_data else None
```

### Skeleton: LIST with Pagination

```python
# src/{module}/repository.py

async def list_all(
    self,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Item], int]:
    """List all items with pagination.
    
    Args:
        skip: Items to skip
        limit: Max items to return
    
    Returns:
        Tuple of (items, total_count)
    """
    all_items = list(self._items.values())
    total = len(all_items)
    items = all_items[skip : skip + limit]
    return [Item.model_validate(t) for t in items], total
```

### Skeleton: FILTER

```python
# src/{module}/repository.py

async def list_by_status(
    self,
    status: str,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Item], int]:
    """List items by status.
    
    Args:
        status: Status to filter by
        skip: Items to skip
        limit: Max items to return
    
    Returns:
        Tuple of (filtered_items, total_count)
    """
    filtered = [t for t in self._items.values() if t["status"] == status]
    total = len(filtered)
    items = filtered[skip : skip + limit]
    return [Item.model_validate(t) for t in items], total
```

### Skeleton: UPDATE

```python
# src/{module}/repository.py

async def update(self, item_id: str, item_update: ItemUpdate) -> Item | None:
    """Update item.
    
    Args:
        item_id: Item ID
        item_update: Update data
    
    Returns:
        Updated item or None if not found
    """
    item_data = self._items.get(item_id)
    if not item_data:
        return None
    
    # Update fields that are provided
    if item_update.name is not None:
        item_data["name"] = item_update.name
    if item_update.status is not None:
        item_data["status"] = item_update.status
    
    # Always update timestamp
    item_data["updated_at"] = datetime.now(UTC)
    
    self._items[item_id] = item_data
    return Item.model_validate(item_data)
```

### Skeleton: DELETE

```python
# src/{module}/repository.py

async def delete(self, item_id: str) -> bool:
    """Delete item.
    
    Args:
        item_id: Item ID
    
    Returns:
        True if deleted, False if not found
    """
    if item_id not in self._items:
        return False
    del self._items[item_id]
    return True
```

### Repository Structure

```python
class MyRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._counter: int = 0
    
    # CRUD operations
    async def create(self, ...):
        pass
    
    async def get_by_id(self, ...):
        pass
    
    async def list_all(self, ...):
        pass
    
    async def update(self, ...):
        pass
    
    async def delete(self, ...):
        pass
    
    # Filtering operations
    async def list_by_status(self, ...):
        pass
    
    async def list_by_user(self, ...):
        pass
    
    # Testing utility
    def reset(self) -> None:
        """Reset repository (clear all data)."""
        self._items.clear()
        self._counter = 0


# Singleton instance at module level
_repository: MyRepository | None = None


def get_my_repository() -> MyRepository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = MyRepository()
    return _repository
```

### Key Rule: Pagination Returns tuple

```python
# ✅ CORRECT
async def list_all(self) -> tuple[list[Item], int]:
    items = [...]
    total = len(items)
    return items, total

# ❌ WRONG
async def list_all(self) -> dict:
    return {"items": [...], "total": len(...)}
```

---

## Pattern 4: Creating Request Models

### Structure

```python
# src/{module}/models.py

from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    """Request model for creating item."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    priority: str = Field(default="MEDIUM")
    category: str = Field(...)  # Required


class ItemUpdate(BaseModel):
    """Request model for updating item."""
    
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    priority: str | None = None
    status: str | None = None
```

### Key Rules

1. **Required fields:** Use `Field(...)`
2. **Optional fields:** Use `Field(None)` or `| None`
3. **String constraints:** `min_length`, `max_length`
4. **Defaults:** `Field(default=value)`
5. **No ID field:** IDs generated by repository/service

---

## Pattern 5: Creating Response Models

### Structure

```python
# src/{module}/models.py

from datetime import datetime
from pydantic import BaseModel, Field

class Item(BaseModel):
    """Response model for item."""
    
    id: str  # Generated ID
    name: str
    description: str | None = None
    priority: str
    category: str
    status: str
    created_at: datetime  # Auto-generated
    updated_at: datetime  # Auto-generated
    created_by: str | None = None
    
    model_config = {"from_attributes": True}  # For ORM support


class ItemList(BaseModel):
    """Response model for paginated list."""
    
    items: list[Item]
    total: int
    skip: int
    limit: int
```

### Key Rules

1. **Include ID:** Always
2. **Include timestamps:** `created_at`, `updated_at`
3. **model_config:** Include `from_attributes = True`
4. **List responses:** Always use pagination tuple: `(items, total)`
5. **Never include:** Passwords, secrets, internal fields

---

## Pattern 6: Raising AppError

### Validation Error

```python
# Raised when input validation fails

if not item_create.name or not item_create.name.strip():
    raise ValidationError(message="Item name is required")
```

### Not Found Error

```python
# Raised when resource doesn't exist

item = await self.repository.get_by_id(item_id)
if not item:
    raise NotFoundError(resource_type="Item", resource_id=item_id)
```

### Business Rule Violation

```python
# Raised when domain rule violated

if item.status == "COMPLETED" and item_update.status == "TODO":
    raise BusinessRuleViolationError(
        message="Cannot move completed item back to TODO",
        rule_name="CANNOT_REOPEN_COMPLETED_ITEMS",
    )
```

### Conflict Error

```python
# Raised when resource already exists (duplicate)

existing = await self.repository.get_by_name(item_create.name)
if existing:
    raise ConflictError(
        resource_type="Item",
        message=f"Item with name '{item_create.name}' already exists",
    )
```

### Error Details

```python
# Include context in error details

raise ValidationError(
    message="Invalid priority value",
    details={"provided_value": item_create.priority, "valid_values": ["LOW", "HIGH"]},
)
```

---

## Pattern 7: Publishing EventBus Events

### Publishing Events

```python
# In service.py after state change

await self.event_bus.publish(
    EventType.ITEM_CREATED,
    {
        "item_id": item.id,
        "name": item.name,
        "created_by": current_user_id,
        "created_at": item.created_at.isoformat(),
    },
)
```

### Event Type Enum

```python
# src/shared/event_bus.py - Add new event type

class EventType(StrEnum):
    # ... existing ...
    
    # New module events
    ITEM_CREATED = "ITEM_CREATED"
    ITEM_UPDATED = "ITEM_UPDATED"
    ITEM_DELETED = "ITEM_DELETED"
```

### Payload Structure

```python
# Event payloads are always dicts with JSON-serializable values

await self.event_bus.publish(
    EventType.ITEM_CREATED,
    {
        "item_id": item.id,  # str
        "name": item.name,  # str
        "created_at": item.created_at.isoformat(),  # ISO string, not datetime object
        "priority": str(item.priority),  # Stringified enum
    },
)
```

### Consuming Events (In Another Module)

```python
# src/alerts/service.py - Subscribe in __init__

class AlertsService:
    def __init__(self, repository: AlertsRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
        
        # Subscribe to events from other modules
        self.event_bus.subscribe(
            EventType.ITEM_CREATED,
            self.handle_item_created,
        )
    
    async def handle_item_created(self, payload: dict) -> None:
        """React to item creation."""
        item_id = payload["item_id"]
        # Trigger alert logic...
```

---

## Pattern 8: Adding Validation

### In Service (Preferred)

```python
# src/{module}/service.py - Business validation

async def create_item(self, item_create: ItemCreate) -> Item:
    # Input validation
    if not item_create.name or not item_create.name.strip():
        raise ValidationError(message="Item name is required")
    
    # Business rule validation
    existing = await self.repository.get_by_name(item_create.name)
    if existing:
        raise ConflictError(resource_type="Item", message="...")
    
    # Proceed if valid
    return await self.repository.create(item_create)
```

### In Model (Pydantic)

```python
# src/{module}/models.py - Structural validation

from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    priority: str = Field(default="MEDIUM")
```

### Rule: Service > Pydantic > Route

1. **Pydantic fields:** Structural/type constraints (min_length, max_length, patterns)
2. **Service validation:** Business logic, uniqueness checks, rule violations
3. **Route validation:** HTTP protocol only (query params, headers)

---

## Pattern 9: Adding Business Rules

### Checking Preconditions

```python
# Check state before allowing operation

async def complete_item(self, item_id: str) -> Item:
    item = await self.repository.get_by_id(item_id)
    
    if item.status == "COMPLETED":
        raise BusinessRuleViolationError(
            message="Item is already completed",
            rule_name="ITEM_ALREADY_COMPLETED",
        )
    
    if item.status == "BLOCKED":
        raise BusinessRuleViolationError(
            message="Cannot complete a blocked item",
            rule_name="CANNOT_COMPLETE_BLOCKED_ITEM",
        )
    
    # Proceed
    return await self.repository.update(item_id, {"status": "COMPLETED"})
```

### Checking Constraints

```python
# Check related state

async def delete_item(self, item_id: str) -> bool:
    item = await self.repository.get_by_id(item_id)
    
    # Check if item is referenced elsewhere
    if item.is_referenced:
        raise BusinessRuleViolationError(
            message="Cannot delete item with active references",
            rule_name="ITEM_HAS_REFERENCES",
        )
    
    return await self.repository.delete(item_id)
```

### Publishing Events for Side Effects

```python
# Publish event that triggers actions in other modules

await self.event_bus.publish(
    EventType.ITEM_COMPLETED,
    {
        "item_id": item.id,
        "completed_at": updated_item.updated_at.isoformat(),
    },
)
# Alerts module subscribes and creates escalation if critical
```

---

## Pattern 10: Implementing Partial-Failure Handling

### Example: Bulk Operation with Failures

```python
# src/{module}/service.py

async def update_items_bulk(
    self,
    item_updates: list[dict],
) -> dict:
    """Update multiple items with failure tracking.
    
    Returns:
        {
            "successful": list[Item],
            "failed": list[{"item_id": str, "error": AppError}],
        }
    """
    successful = []
    failed = []
    
    for update in item_updates:
        try:
            item_id = update["id"]
            updated = await self.update_item(item_id, update)
            successful.append(updated)
        except AppError as e:
            failed.append({
                "item_id": update.get("id"),
                "error_code": e.error_code,
                "message": e.message,
            })
    
    # Publish event even with partial success
    if successful:
        await self.event_bus.publish(
            EventType.ITEMS_UPDATED,
            {
                "count": len(successful),
                "failed_count": len(failed),
            },
        )
    
    return {
        "successful": successful,
        "failed": failed,
    }
```

### Response Model

```python
# src/{module}/models.py

class BulkUpdateResult(BaseModel):
    successful: list[Item]
    failed: list[dict]  # Contains error details
```

### Route Handler

```python
# src/{module}/routes.py

@router.post("/items/bulk-update", response_model=BulkUpdateResult)
async def bulk_update_items(
    updates: list[dict],
    service: MyService = Depends(get_my_service),
) -> BulkUpdateResult:
    """Update multiple items (partial success allowed)."""
    result = await service.update_items_bulk(updates)
    return BulkUpdateResult(**result)
```

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Business logic in routes | Move to service |
| Raw exceptions in service | Raise AppError subclasses |
| Repositories publish events | Move to service |
| Routes access repositories | Go through service |
| Missing type hints | Add full type annotations |
| Not awaiting async calls | Use `await` |
| Missing error handling in routes | Wrap in try/except, catch AppError |
| Returning raw dicts | Return Pydantic models |
| List pagination returns list | Return tuple[list, total] |
| Missing `model_config` on responses | Add `from_attributes = True` |

---

## Reference

### Import Template

```python
# src/{module}/service.py

from src.{module}.models import Item, ItemCreate, ItemUpdate
from src.{module}.repository import MyRepository, get_my_repository
from src.shared.errors import (
    AppError,
    BusinessRuleViolationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.shared.event_bus import EventBus, EventType, get_event_bus
```

### Error Response Example

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Item name is required",
    "details": {}
}
```

---

*For coding conventions, see [[coding-conventions]]. For testing patterns, see [[how-to-test]]. For architectural principles, see [[architecture-principles]].*
