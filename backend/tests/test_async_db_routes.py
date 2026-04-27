import inspect

from app.api.endpoints import admin, auth, loan, user
from app.core.database import get_db


def _find_db_routes(router):
    result = []
    for route in router.routes:
        endpoint = route.endpoint
        deps = getattr(route, "dependant", None)
        dependencies = deps.dependencies if deps else []
        has_sync_db = any(getattr(item, "call", None) is get_db for item in dependencies)
        result.append((route.path, endpoint, has_sync_db))
    return result


def test_auth_routes_should_use_async_and_not_depend_on_sync_db():
    routes = _find_db_routes(auth.router)
    db_routes = [item for item in routes if "/channels/" in item[0] or "/login" in item[0]]
    assert db_routes
    for path, endpoint, has_sync_db in db_routes:
        assert inspect.iscoroutinefunction(endpoint), f"{path} should be async def"
        assert has_sync_db is False, f"{path} should not depend on get_db"


def test_loan_routes_should_use_async_and_not_depend_on_sync_db():
    routes = _find_db_routes(loan.router)
    assert routes
    for path, endpoint, has_sync_db in routes:
        assert inspect.iscoroutinefunction(endpoint), f"{path} should be async def"
        assert has_sync_db is False, f"{path} should not depend on get_db"


def test_user_routes_should_use_async_and_not_depend_on_sync_db():
    routes = _find_db_routes(user.router)
    assert routes
    for path, endpoint, has_sync_db in routes:
        assert inspect.iscoroutinefunction(endpoint), f"{path} should be async def"
        assert has_sync_db is False, f"{path} should not depend on get_db"


def test_admin_partial_routes_should_use_async_and_not_depend_on_sync_db():
    routes = _find_db_routes(admin.router)
    targets = {
        "/login",
        "/me",
        "/stats",
        "/repayment-stats",
        "/project-cash-insights",
        "/loans",
        "/users",
        "/loans/{loan_id}/ledger",
        "/users/{user_id}",
        "/risk/report",
        "/channels",
        "/channels/{channel_id}",
        "/products",
        "/products/{product_id}",
        "/ecard-pool",
        "/ecard-pool/batch-upload",
        "/ecard-pool/template",
        "/ecard-pool/{item_id}",
        "/loans/{loan_id}/review",
        "/loans/{loan_id}",
        "/loans/{loan_id}/disburse",
        "/loans/{loan_id}/settle",
        "/loans/{loan_id}/finance-reconcile",
        "/loans/{loan_id}/remind",
        "/loans/{loan_id}/collect",
        "/loans/{loan_id}/ack-repay-attempt",
        "/loan-assignees",
        "/loans/{loan_id}/assign",
        "/admin-users",
        "/admin-users/{admin_id}",
    }
    selected = [item for item in routes if item[0] in targets]
    assert selected
    for path, endpoint, has_sync_db in selected:
        assert inspect.iscoroutinefunction(endpoint), f"{path} should be async def"
        assert has_sync_db is False, f"{path} should not depend on get_db"
