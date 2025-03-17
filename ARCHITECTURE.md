# Payment Gateway System Architecture

## Overview

The Payment Gateway system has been refactored to follow a Controller-Service-Repository (CSR) pattern, which provides a clean separation of concerns and improves code maintainability, testability, and scalability.

## Three-Tier Architecture

The system is organized into three distinct layers:

### 1. Repository Layer

The Repository Layer is responsible for all data access operations. It provides a clean abstraction over the database and handles all CRUD operations.

- Manages all database interactions
- Maps database entities to domain models
- Provides data filtering, searching, and ordering capabilities
- Handles database exceptions and transaction management

### 2. Service Layer

The Service Layer contains the core business logic of the application. It:

- Orchestrates the use of repositories
- Implements business rules and validations
- Coordinates transactions across multiple repositories
- Handles permissions and access control
- Provides a clean interface for controllers

### 3. Controller Layer

The Controller Layer handles HTTP requests and responses. It:

- Maps HTTP requests to service calls
- Formats responses in appropriate formats (JSON)
- Handles HTTP-specific concerns like status codes and headers
- Manages request validation and authentication

## Flow Diagram

```
HTTP Request
    │
    ▼
┌────────────────┐
│   Controller   │  Handles HTTP requests/responses
└────────────────┘
         │
         ▼
┌────────────────┐
│    Service     │  Implements business logic
└────────────────┘
         │
         ▼
┌────────────────┐
│   Repository   │  Manages data access
└────────────────┘
         │
         ▼
┌────────────────┐
│   Database     │  Stores data
└────────────────┘
```

## Directory Structure

```
app/
├── controllers/        # Controllers handle HTTP requests/responses
│   ├── __init__.py
│   ├── bank_controller.py
│   └── bank_account_controller.py
│
├── services/           # Services implement business logic
│   ├── __init__.py
│   ├── bank_service.py
│   └── bank_account_service.py
│
├── repositories/       # Repositories manage data access
│   ├── __init__.py
│   ├── bank_repository.py
│   └── bank_account_repository.py
│
├── models/             # Django models
│   ├── __init__.py
│   └── ...
│
└── api/                # API definitions and serializers
    ├── __init__.py
    ├── serializers.py
    ├── urls.py
    └── ...
```

## Benefits of This Architecture

- **Separation of Concerns**: Each layer has a single responsibility.
- **Testability**: Each layer can be tested in isolation.
- **Maintainability**: Changes to one layer don't affect others.
- **Flexibility**: Easy to swap out implementations (e.g., different database).
- **Scalability**: Facilitates splitting the application into microservices.

## Implementation Examples

### Repository Example

```python
class BankRepository:
    @staticmethod
    def get_by_id(bank_id: int) -> Optional[Bank]:
        try:
            return Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return None
```

### Service Example

```python
class BankService:
    @staticmethod
    def get_bank_by_id(bank_id: int) -> Optional[Bank]:
        return BankRepository.get_by_id(bank_id)
    
    @staticmethod
    def create_bank(data: Dict[str, Any], user: User) -> Bank:
        # Validate data
        if 'name' not in data:
            raise ValueError("Bank name is required")
        
        # Create bank
        return BankRepository.create(data)
```

### Controller Example

```python
class BankController(APIView):
    def get(self, request: Request, bank_id: int = None) -> Response:
        try:
            bank = BankService.get_bank_by_id(bank_id)
            if not bank:
                return Response({"error": "Bank not found"}, status=404)
            
            serializer = BankSerializer(bank)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
``` 