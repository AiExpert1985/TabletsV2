import 'package:client/core/authorization/permissions.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';

/// Role-to-Permission mappings (Single Source of Truth).
///
/// This file defines what permissions each role has.
/// Uses PermissionGroups for type-safety and easier maintenance.
///
/// Single role system - each user has ONE role that maps to a permission set.
class RolePermissions {
  // Prevent instantiation
  RolePermissions._();

  /// Role permission mappings
  static final Map<String, Set<Permission>> _rolePermissions = {
    // System Admin: ALL permissions (including company management)
    UserRole.systemAdmin: PermissionGroups.allPermissions,

    // Company Admin: Full access within company
    UserRole.companyAdmin: {
      ...PermissionGroups.userManagement,
      ...PermissionGroups.productManagement,
      ...PermissionGroups.invoiceManagement,
      ...PermissionGroups.purchaseManagement,
      ...PermissionGroups.warehouseManagement,
      ...PermissionGroups.financialReporting,
      Permission.viewAuditLogs,
    },

    // Accountant: Financial operations and reports
    UserRole.accountant: {
      ...PermissionGroups.userReadOnly,
      ...PermissionGroups.productReadOnly,
      ...PermissionGroups.accountingPermissions,
    },

    // Sales Manager: Manage sales and invoices
    UserRole.salesManager: {
      ...PermissionGroups.userReadOnly,
      ...PermissionGroups.salesPermissions,
    },

    // Warehouse Keeper: Manage inventory and warehouse
    UserRole.warehouseKeeper: PermissionGroups.warehouseKeeperPermissions,

    // Salesperson: Create/view invoices only
    UserRole.salesperson: {
      ...PermissionGroups.productReadOnly,
      Permission.viewInvoices,
      Permission.createInvoices,
      ...PermissionGroups.warehouseReadOnly,
    },

    // Viewer: Read-only access
    UserRole.viewer: {
      ...PermissionGroups.userReadOnly,
      ...PermissionGroups.productReadOnly,
      ...PermissionGroups.invoiceReadOnly,
      ...PermissionGroups.purchaseReadOnly,
      ...PermissionGroups.warehouseReadOnly,
      ...PermissionGroups.reportingReadOnly,
    },
  };

  /// Get all permissions for a user role
  static Set<Permission> getPermissionsForRole(String role) {
    return _rolePermissions[role] ?? {};
  }
}
