"""Tests for permission-based authorization checker."""
import pytest
from uuid import uuid4

from features.users.models import User
from core.enums import UserRole
from features.authorization.permissions import Permission
from features.authorization.permission_checker import (
    get_user_permissions,
    has_permission,
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_system_admin,
    require_company_admin,
)
from core.exceptions import PermissionDeniedException


# ============================================================================
# Test get_user_permissions
# ============================================================================

def test_system_admin_has_all_permissions():
    """System admin gets all permissions."""
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000001",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    permissions = get_user_permissions(user)

    # System admin has all permissions
    assert Permission.VIEW_USERS in permissions
    assert Permission.CREATE_USERS in permissions
    assert Permission.VIEW_PRODUCTS in permissions
    assert Permission.CREATE_COMPANIES in permissions


def test_company_admin_with_admin_role():
    """Company admin with admin company role gets appropriate permissions."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000002",
        hashed_password="hash",
        role=UserRole.COMPANY_ADMIN,
        company_id=company_id,
        is_active=True,
    )

    permissions = get_user_permissions(user)

    # Should have admin permissions
    assert Permission.VIEW_USERS in permissions
    assert Permission.EDIT_USERS in permissions
    assert Permission.CREATE_PRODUCTS in permissions

    # Should NOT have system admin permissions
    assert Permission.CREATE_COMPANIES not in permissions


def test_user_with_viewer_role():
    """Regular user with viewer role gets read-only permissions."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000003",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    permissions = get_user_permissions(user)

    # Should have view permissions
    assert Permission.VIEW_USERS in permissions
    assert Permission.VIEW_PRODUCTS in permissions

    # Should NOT have write permissions
    assert Permission.CREATE_USERS not in permissions
    assert Permission.CREATE_PRODUCTS not in permissions


def test_user_with_salesperson_role():
    """User with salesperson role gets appropriate permissions."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000004",
        hashed_password="hash",
        role=UserRole.SALESPERSON,
        company_id=company_id,
        is_active=True,
    )

    permissions = get_user_permissions(user)

    # Should have salesperson permissions
    assert Permission.VIEW_PRODUCTS in permissions
    assert Permission.CREATE_INVOICES in permissions

    # Should NOT have product management permissions
    assert Permission.CREATE_PRODUCTS not in permissions
    assert Permission.DELETE_PRODUCTS not in permissions


def test_user_with_accountant_role():
    """User with accountant role gets financial permissions."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000005",
        hashed_password="hash",
        role=UserRole.ACCOUNTANT,
        company_id=company_id,
        is_active=True,
    )

    permissions = get_user_permissions(user)

    # Should have view permissions
    assert Permission.VIEW_USERS in permissions
    assert Permission.VIEW_PRODUCTS in permissions

    # Should have financial permissions
    assert Permission.VIEW_FINANCIALS in permissions
    assert Permission.EXPORT_REPORTS in permissions

    # Should NOT have create/edit permissions
    assert Permission.CREATE_USERS not in permissions
    assert Permission.CREATE_PRODUCTS not in permissions


# ============================================================================
# Test has_permission
# ============================================================================

def test_has_permission_true():
    """has_permission returns True when user has permission."""
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000006",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    assert has_permission(user, Permission.VIEW_USERS) is True
    assert has_permission(user, Permission.CREATE_COMPANIES) is True


def test_has_permission_false():
    """has_permission returns False when user lacks permission."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000007",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    assert has_permission(user, Permission.VIEW_USERS) is True
    assert has_permission(user, Permission.CREATE_USERS) is False
    assert has_permission(user, Permission.DELETE_PRODUCTS) is False


# ============================================================================
# Test require_permission
# ============================================================================

def test_require_permission_allows_when_has_permission():
    """require_permission allows when user has permission."""
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000008",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    # Should not raise
    require_permission(user, Permission.VIEW_USERS)
    require_permission(user, Permission.CREATE_COMPANIES)


def test_require_permission_denies_when_lacks_permission():
    """require_permission raises when user lacks permission."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000009",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    # Should raise
    with pytest.raises(PermissionDeniedException) as exc:
        require_permission(user, Permission.DELETE_USERS)

    assert "Missing required permission" in str(exc.value)


def test_require_permission_checks_company_isolation():
    """require_permission checks company isolation."""
    company_id = uuid4()
    other_company_id = uuid4()

    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000010",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    # Same company - should not raise
    require_permission(user, Permission.VIEW_PRODUCTS, company_id)

    # Different company - should raise
    with pytest.raises(PermissionDeniedException) as exc:
        require_permission(user, Permission.VIEW_PRODUCTS, other_company_id)

    assert "Cannot access other company's data" in str(exc.value)


def test_require_permission_system_admin_bypasses_company_check():
    """System admin can access any company."""
    other_company_id = uuid4()

    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000011",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    # Should not raise even for different company
    require_permission(user, Permission.VIEW_PRODUCTS, other_company_id)


# ============================================================================
# Test require_any_permission
# ============================================================================

def test_require_any_permission_allows_when_has_one():
    """require_any_permission allows when user has at least one permission."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000012",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    # User has VIEW_PRODUCTS but not CREATE_PRODUCTS
    require_any_permission(
        user,
        [Permission.VIEW_PRODUCTS, Permission.CREATE_PRODUCTS]
    )


def test_require_any_permission_denies_when_has_none():
    """require_any_permission raises when user has none."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000013",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    # Viewer cannot delete
    with pytest.raises(PermissionDeniedException) as exc:
        require_any_permission(
            user,
            [Permission.DELETE_USERS, Permission.DELETE_PRODUCTS]
        )

    assert "Need one of" in str(exc.value)


# ============================================================================
# Test require_all_permissions
# ============================================================================

def test_require_all_permissions_allows_when_has_all():
    """require_all_permissions allows when user has all permissions."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000014",
        hashed_password="hash",
        role=UserRole.COMPANY_ADMIN,
        company_id=company_id,
        is_active=True,
    )

    # Admin has both
    require_all_permissions(
        user,
        [Permission.VIEW_PRODUCTS, Permission.CREATE_PRODUCTS]
    )


def test_require_all_permissions_denies_when_missing_one():
    """require_all_permissions raises when missing any permission."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000015",
        hashed_password="hash",
        role=UserRole.SALESPERSON,
        company_id=company_id,
        is_active=True,
    )

    # Salesperson can view and create but not delete
    with pytest.raises(PermissionDeniedException) as exc:
        require_all_permissions(
            user,
            [Permission.VIEW_PRODUCTS, Permission.DELETE_PRODUCTS]
        )

    assert "Missing required permissions" in str(exc.value)


# ============================================================================
# Test require_system_admin
# ============================================================================

def test_require_system_admin_allows_system_admin():
    """require_system_admin allows system admin."""
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000016",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    require_system_admin(user)  # Should not raise


def test_require_system_admin_denies_others():
    """require_system_admin denies non-system-admin."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000017",
        hashed_password="hash",
        role=UserRole.COMPANY_ADMIN,
        company_id=company_id,
        is_active=True,
    )

    with pytest.raises(PermissionDeniedException) as exc:
        require_system_admin(user)

    assert "System administrator access required" in str(exc.value)


# ============================================================================
# Test require_company_admin
# ============================================================================

def test_require_company_admin_allows_system_admin():
    """require_company_admin allows system admin."""
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000018",
        hashed_password="hash",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )

    require_company_admin(user)  # Should not raise


def test_require_company_admin_allows_company_admin():
    """require_company_admin allows company admin."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000019",
        hashed_password="hash",
        role=UserRole.COMPANY_ADMIN,
        company_id=company_id,
        is_active=True,
    )

    require_company_admin(user)  # Should not raise


def test_require_company_admin_denies_regular_user():
    """require_company_admin denies regular user."""
    company_id = uuid4()
    user = User(
        id=uuid4()
        name="Test User",,
        phone_number="+9647700000020",
        hashed_password="hash",
        role=UserRole.VIEWER,
        company_id=company_id,
        is_active=True,
    )

    with pytest.raises(PermissionDeniedException) as exc:
        require_company_admin(user)

    assert "Administrator access required" in str(exc.value)
