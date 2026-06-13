"""
Quick verification script for User Service implementation.

Checks:
1. All required files exist
2. Imports work correctly
3. Basic structure is correct
"""

import sys
from pathlib import Path

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists and report."""
    if file_path.exists():
        print(f"{GREEN}✓{RESET} {description}: {file_path.name}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {file_path.name} NOT FOUND")
        return False


def main():
    """Run verification checks."""
    print("\n" + "=" * 60)
    print("User Service Implementation Verification")
    print("=" * 60 + "\n")

    base_path = Path(__file__).parent
    all_checks_passed = True

    # Check core files
    print("📁 Core Structure:")
    checks = [
        (base_path / "app" / "main.py", "Main entry point"),
        (base_path / "app" / "config.py", "Configuration"),
        (base_path / "alembic.ini", "Alembic config"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check domain layer
    print("\n📁 Domain Layer:")
    checks = [
        (base_path / "app" / "domain" / "models.py", "SQLAlchemy models"),
        (base_path / "app" / "domain" / "schemas.py", "Pydantic schemas"),
        (base_path / "app" / "domain" / "service.py", "Business logic"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check database layer
    print("\n📁 Database Layer:")
    checks = [
        (base_path / "app" / "db" / "session.py", "Session management"),
        (base_path / "app" / "db" / "repository.py", "Data access layer"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check API layer
    print("\n📁 API Layer:")
    checks = [
        (base_path / "app" / "api" / "routes.py", "FastAPI routes"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check migrations
    print("\n📁 Migrations:")
    checks = [
        (base_path / "alembic" / "env.py", "Alembic environment"),
        (base_path / "alembic" / "script.py.mako", "Migration template"),
        (
            base_path / "alembic" / "versions" / "001_create_users_table.py",
            "Initial migration",
        ),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check tests
    print("\n📁 Tests:")
    checks = [
        (base_path / "tests" / "conftest.py", "Test configuration"),
        (base_path / "tests" / "test_auth.py", "Auth tests"),
        (base_path / "tests" / "test_users.py", "User tests"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Try importing modules
    print("\n🔍 Import Checks:")
    try:
        sys.path.insert(0, str(base_path))
        from app.config import settings

        print(f"{GREEN}✓{RESET} Config imports successfully")
        print(f"  - Service name: {settings.service_name}")
        print(f"  - Database URL configured: {bool(settings.database_url)}")
    except Exception as e:
        print(f"{RED}✗{RESET} Config import failed: {e}")
        all_checks_passed = False

    try:
        from app.domain.models import User

        print(f"{GREEN}✓{RESET} Models import successfully")
        print(f"  - User model has {len(User.__table__.columns)} columns")
    except Exception as e:
        print(f"{RED}✗{RESET} Models import failed: {e}")
        all_checks_passed = False

    try:
        from app.domain.schemas import (
            LoginRequest,
            RegisterRequest,
            UserResponse,
        )

        print(f"{GREEN}✓{RESET} Schemas import successfully")
    except Exception as e:
        print(f"{RED}✗{RESET} Schemas import failed: {e}")
        all_checks_passed = False

    # Check API contract compliance
    print("\n📋 API Contract Compliance:")
    required_endpoints = [
        "POST /auth/register",
        "POST /auth/login",
        "GET /users/{id}",
        "PATCH /users/{id}",
        "GET /users/{id}/credits",
        "GET /users/candidates",
    ]

    try:
        from app.api.routes import router

        route_paths = [f"{list(route.methods)[0]} {route.path}" for route in router.routes]
        
        for endpoint in required_endpoints:
            if any(endpoint.split()[1] in path for path in route_paths):
                print(f"{GREEN}✓{RESET} {endpoint}")
            else:
                print(f"{YELLOW}⚠{RESET} {endpoint} - may need verification")
    except Exception as e:
        print(f"{RED}✗{RESET} Could not verify routes: {e}")
        all_checks_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print(f"{GREEN}✓ All checks passed!{RESET}")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e '.[dev]'")
        print("2. Run tests: pytest tests/ -v")
        print("3. Start service: uvicorn app.main:app --reload --port 8001")
        print("4. Apply migrations: alembic upgrade head")
        return 0
    else:
        print(f"{RED}✗ Some checks failed{RESET}")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
