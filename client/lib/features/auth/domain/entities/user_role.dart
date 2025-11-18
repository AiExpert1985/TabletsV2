/// User role constants
///
/// These match the backend UserRole enum values.
class UserRole {
  // Prevent instantiation
  UserRole._();

  /// System administrator - full access to all companies
  static const String systemAdmin = 'system_admin';

  /// Company administrator - full access within their company
  static const String companyAdmin = 'company_admin';

  /// Accountant - financial operations and reports
  static const String accountant = 'accountant';

  /// Sales manager - manage sales and invoices
  static const String salesManager = 'sales_manager';

  /// Warehouse keeper - manage inventory and warehouse
  static const String warehouseKeeper = 'warehouse_keeper';

  /// Salesperson - create/view invoices
  static const String salesperson = 'salesperson';

  /// Viewer - read-only access
  static const String viewer = 'viewer';

  /// All valid roles
  static const List<String> allRoles = [
    systemAdmin,
    companyAdmin,
    accountant,
    salesManager,
    warehouseKeeper,
    salesperson,
    viewer,
  ];

  /// Get a human-readable display name for a role
  static String displayName(String role) {
    switch (role) {
      case systemAdmin:
        return 'System Admin';
      case companyAdmin:
        return 'Company Admin';
      case accountant:
        return 'Accountant';
      case salesManager:
        return 'Sales Manager';
      case warehouseKeeper:
        return 'Warehouse Keeper';
      case salesperson:
        return 'Salesperson';
      case viewer:
        return 'Viewer';
      default:
        return role;
    }
  }

  /// Check if a role is valid
  static bool isValid(String role) => allRoles.contains(role);
}
