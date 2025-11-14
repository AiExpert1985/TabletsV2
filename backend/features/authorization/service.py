"""
Authorization Service - Core permission checking logic.

Implements two-tier permission system with role aggregation.
"""
from features.auth.models import User, UserRole
from features.authorization.permissions import Permission, CompanyRole
from features.authorization.role_permissions import get_all_permissions_for_user
from features.logging.logger import get_logger

logger = get_logger(__name__)


class AuthorizationService:
    """
    Service for checking user permissions.

    Implements:
    - Two-tier permission model (system + company roles)
    - Permission aggregation (multiple roles combine)
    - Default deny security model
    - Status-based access control
    """

    def __init__(self, user: User | None):
        """
        Initialize authorization service for a user.

        Args:
            user: Current user (None = no permissions)
        """
        self.user = user
        self._permissions: set[Permission] | None = None

    @property
    def permissions(self) -> set[Permission]:
        """
        Get aggregated permissions for the user.

        Lazily calculated and cached.

        Returns:
            Set of all permissions the user has
        """
        if self._permissions is None:
            self._permissions = self._calculate_permissions()
        return self._permissions

    def _calculate_permissions(self) -> set[Permission]:
        """
        Calculate all permissions for the user.

        Security rules:
        - Null user = no permissions
        - Inactive user = no permissions
        - System admin = all permissions
        - Company users = permissions from company roles

        Returns:
            Set of permissions
        """
        # Default deny: no user = no permissions
        if self.user is None:
            logger.debug("Authorization: No user, denying all permissions")
            return set()

        # Status check: inactive users get zero permissions
        if not self.user.is_active:
            logger.warning(
                f"Authorization: User {self.user.id} is inactive, denying all permissions"
            )
            return set()

        # Parse company roles from JSON list
        company_roles: list[CompanyRole] = []
        for role_str in self.user.company_roles:
            try:
                company_roles.append(CompanyRole(role_str))
            except ValueError:
                logger.warning(
                    f"Authorization: Invalid company role '{role_str}' for user {self.user.id}"
                )
                continue

        # Aggregate permissions from system role + company roles
        permissions = get_all_permissions_for_user(
            system_role=self.user.role,
            company_roles=company_roles
        )

        logger.debug(
            f"Authorization: User {self.user.id} has {len(permissions)} permissions "
            f"(system_role={self.user.role.value}, company_roles={[r.value for r in company_roles]})"
        )

        return permissions

    def has_permission(self, permission: Permission | str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission to check (enum or string)

        Returns:
            True if user has permission, False otherwise
        """
        # Convert string to Permission enum if needed
        if isinstance(permission, str):
            try:
                permission = Permission(permission)
            except ValueError:
                logger.warning(f"Authorization: Invalid permission string '{permission}'")
                return False

        has_perm = permission in self.permissions

        if not has_perm:
            logger.debug(
                f"Authorization DENIED: User {self.user.id if self.user else 'None'} "
                f"does not have permission '{permission.value}'"
            )

        return has_perm

    def has_any_permission(self, permissions: list[Permission | str]) -> bool:
        """
        Check if user has ANY of the given permissions.

        Args:
            permissions: List of permissions to check

        Returns:
            True if user has at least one permission
        """
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: list[Permission | str]) -> bool:
        """
        Check if user has ALL of the given permissions.

        Args:
            permissions: List of permissions to check

        Returns:
            True if user has all permissions
        """
        return all(self.has_permission(p) for p in permissions)

    def is_system_admin(self) -> bool:
        """
        Check if user is a system administrator.

        Returns:
            True if user has system admin role
        """
        return self.user is not None and self.user.role == UserRole.SYSTEM_ADMIN

    def get_permission_list(self) -> list[str]:
        """
        Get list of permission strings for the user.

        Useful for sending to client.

        Returns:
            List of permission values (e.g., ["users.view", "users.create"])
        """
        return [p.value for p in self.permissions]


def create_authorization_service(user: User | None) -> AuthorizationService:
    """
    Factory function to create AuthorizationService.

    Args:
        user: Current user

    Returns:
        AuthorizationService instance
    """
    return AuthorizationService(user)
