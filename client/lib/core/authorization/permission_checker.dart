import 'package:client/core/authorization/permissions.dart';
import 'package:client/core/authorization/role_permissions.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';

/// Permission-based authorization checker.
///
/// Centralized permission checking utility with single-role system.
/// Supports company-aware authorization.
///
/// Usage:
///   if (PermissionChecker.hasPermission(user, Permission.createUsers)) {
///     // User can create users
///   }
class PermissionChecker {
  // Prevent instantiation
  PermissionChecker._();

  /// Get all permissions for a user based on their role
  static Set<Permission> getUserPermissions(User user) {
    return RolePermissions.getPermissionsForRole(user.role);
  }

  /// Check if user has a specific permission
  static bool hasPermission(User user, Permission permission) {
    final userPermissions = getUserPermissions(user);
    return userPermissions.contains(permission);
  }

  /// Check if user has ANY of the required permissions (OR logic)
  static bool hasAnyPermission(User user, List<Permission> permissions) {
    final userPermissions = getUserPermissions(user);
    return permissions.any((p) => userPermissions.contains(p));
  }

  /// Check if user has ALL of the required permissions (AND logic)
  static bool hasAllPermissions(User user, List<Permission> permissions) {
    final userPermissions = getUserPermissions(user);
    return permissions.every((p) => userPermissions.contains(p));
  }

  /// Check if user is system admin
  static bool isSystemAdmin(User user) {
    return user.role == UserRole.systemAdmin;
  }

  /// Check if user is admin (system admin or company admin)
  static bool isAdmin(User user) {
    return user.role == UserRole.systemAdmin ||
           user.role == UserRole.companyAdmin;
  }

  /// Check if user can access data from a specific company
  ///
  /// System admins can access any company.
  /// Regular users can only access their own company's data.
  static bool canAccessCompany(User user, String? companyId) {
    // System admin can access any company
    if (isSystemAdmin(user)) {
      return true;
    }

    // Regular users must match company
    return user.companyId == companyId;
  }

  /// Check if user has permission and company access
  ///
  /// This combines permission check with company isolation check.
  static bool canPerformAction(
    User user,
    Permission permission, {
    String? companyId,
  }) {
    // Check permission first
    if (!hasPermission(user, permission)) {
      return false;
    }

    // If company check is needed, verify access
    if (companyId != null) {
      return canAccessCompany(user, companyId);
    }

    return true;
  }
}
