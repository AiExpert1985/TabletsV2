/// Permission system for granular CRUD-based access control.
///
/// Defines all permissions in the system organized by feature domain.
/// Uses type-safe enums to avoid string-based errors.
enum Permission {
  // ========================================================================
  // User Management
  // ========================================================================
  viewUsers('users.view'),
  createUsers('users.create'),
  editUsers('users.edit'),
  deleteUsers('users.delete'),

  // ========================================================================
  // Company Management (System Admin only)
  // ========================================================================
  viewCompanies('companies.view'),
  createCompanies('companies.create'),
  editCompanies('companies.edit'),
  deleteCompanies('companies.delete'),

  // ========================================================================
  // Products/Inventory
  // ========================================================================
  viewProducts('products.view'),
  createProducts('products.create'),
  editProducts('products.edit'),
  deleteProducts('products.delete'),

  // ========================================================================
  // Sales/Invoices
  // ========================================================================
  viewInvoices('invoices.view'),
  createInvoices('invoices.create'),
  editInvoices('invoices.edit'),
  deleteInvoices('invoices.delete'),

  // ========================================================================
  // Purchases
  // ========================================================================
  viewPurchases('purchases.view'),
  createPurchases('purchases.create'),
  editPurchases('purchases.edit'),
  deletePurchases('purchases.delete'),

  // ========================================================================
  // Warehouse Management
  // ========================================================================
  viewWarehouse('warehouse.view'),
  manageWarehouse('warehouse.manage'),

  // ========================================================================
  // Accounting/Reports
  // ========================================================================
  viewReports('reports.view'),
  exportReports('reports.export'),
  viewFinancials('financials.view'),

  // ========================================================================
  // System Administration
  // ========================================================================
  viewAuditLogs('audit.view'),
  viewSystemSettings('settings.view'),
  editSystemSettings('settings.edit');

  const Permission(this.value);
  final String value;

  /// Get Permission by string value
  static Permission? fromValue(String value) {
    try {
      return Permission.values.firstWhere((p) => p.value == value);
    } catch (e) {
      return null;
    }
  }
}

/// Permission groups - organized sets for easier management
class PermissionGroups {
  // Prevent instantiation
  PermissionGroups._();

  // User Management
  static const Set<Permission> userManagement = {
    Permission.viewUsers,
    Permission.createUsers,
    Permission.editUsers,
    Permission.deleteUsers,
  };

  static const Set<Permission> userReadOnly = {
    Permission.viewUsers,
  };

  // Company Management (System Admin only)
  static const Set<Permission> companyManagement = {
    Permission.viewCompanies,
    Permission.createCompanies,
    Permission.editCompanies,
    Permission.deleteCompanies,
  };

  // Product/Inventory Management
  static const Set<Permission> productManagement = {
    Permission.viewProducts,
    Permission.createProducts,
    Permission.editProducts,
    Permission.deleteProducts,
  };

  static const Set<Permission> productReadOnly = {
    Permission.viewProducts,
  };

  // Sales/Invoice Management
  static const Set<Permission> invoiceManagement = {
    Permission.viewInvoices,
    Permission.createInvoices,
    Permission.editInvoices,
    Permission.deleteInvoices,
  };

  static const Set<Permission> invoiceReadOnly = {
    Permission.viewInvoices,
  };

  // Purchase Management
  static const Set<Permission> purchaseManagement = {
    Permission.viewPurchases,
    Permission.createPurchases,
    Permission.editPurchases,
    Permission.deletePurchases,
  };

  static const Set<Permission> purchaseReadOnly = {
    Permission.viewPurchases,
  };

  // Warehouse Management
  static const Set<Permission> warehouseManagement = {
    Permission.viewWarehouse,
    Permission.manageWarehouse,
  };

  static const Set<Permission> warehouseReadOnly = {
    Permission.viewWarehouse,
  };

  // Financial/Reporting
  static const Set<Permission> financialReporting = {
    Permission.viewReports,
    Permission.exportReports,
    Permission.viewFinancials,
  };

  static const Set<Permission> reportingReadOnly = {
    Permission.viewReports,
  };

  // System Administration
  static const Set<Permission> systemAdminOnly = {
    Permission.viewAuditLogs,
    Permission.viewSystemSettings,
    Permission.editSystemSettings,
  };

  // Common combinations
  static final Set<Permission> accountingPermissions = {
    ...invoiceReadOnly,
    ...purchaseReadOnly,
    ...financialReporting,
  };

  static final Set<Permission> salesPermissions = {
    ...productReadOnly,
    ...invoiceManagement,
    ...reportingReadOnly,
  };

  static final Set<Permission> warehouseKeeperPermissions = {
    ...productManagement,
    ...warehouseManagement,
    ...purchaseReadOnly,
  };

  // All permissions (for system admin)
  static final Set<Permission> allPermissions = Permission.values.toSet();
}
