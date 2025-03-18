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

The refactored system follows this directory structure for each app:

```
app/
├── controllers/        # Controllers handle HTTP requests/responses
│   ├── __init__.py
│   └── *_controller.py
│
├── services/           # Services implement business logic
│   ├── __init__.py
│   └── *_service.py
│
├── repositories/       # Repositories manage data access
│   ├── __init__.py
│   └── *_repository.py
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

## Implemented Modules

### Bank Module

The Bank module manages bank and bank account information:

- **Repositories**:
  - `BankRepository`: Handles database operations for the Bank model
  - `BankAccountRepository`: Handles database operations for the BankAccount model

- **Services**:
  - `BankService`: Implements business logic for bank management
  - `BankAccountService`: Implements business logic for bank account management

- **Controllers**:
  - `BankController`: Handles HTTP requests for bank management
  - `BankStatusController`: Handles HTTP requests for toggling bank status
  - `BankAccountController`: Handles HTTP requests for bank account management
  - `BankAccountStatusController`: Handles HTTP requests for toggling account status
  - `BankAccountBalanceController`: Handles HTTP requests for updating account balance

### Payout Module

The Payout module manages payment transactions:

- **Repositories**:
  - `PayoutRepository`: Handles database operations for the Payout model

- **Services**:
  - `PayoutService`: Implements business logic for payout management

- **Controllers**:
  - `PayoutController`: Handles HTTP requests for payout management
  - `PayoutProcessController`: Handles HTTP requests for processing payouts
  - `PayoutCancelController`: Handles HTTP requests for cancelling payouts
  - `PayoutBulkProcessController`: Handles HTTP requests for bulk processing
  - `PayoutStatsController`: Handles HTTP requests for payout statistics

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

## Testing Strategy

This architecture makes testing easier by allowing each layer to be tested independently:

1. **Repository Tests**: Focus on database interactions, using Django's test database.
2. **Service Tests**: Mock the repositories to test business logic in isolation.
3. **Controller Tests**: Mock the services to test HTTP handling.

## Future Considerations

As the application grows, consider:

1. **Dependency Injection**: Implement a proper DI framework to make testing easier.
2. **Async Processing**: Move long-running tasks to background workers.
3. **Microservices**: Split the monolith into separate services based on domains. 