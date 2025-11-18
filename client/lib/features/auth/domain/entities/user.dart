/// User entity
class User {
  final String id;
  final String phoneNumber;
  final String? email;
  final String? companyId;  // NULL for system admin
  final String role;  // system_admin, company_admin, accountant, sales_manager, warehouse_keeper, salesperson, viewer
  final List<String> permissions;  // Aggregated permissions
  final bool isActive;
  final bool isPhoneVerified;
  final DateTime createdAt;
  final DateTime? lastLoginAt;

  User({
    required this.id,
    required this.phoneNumber,
    this.email,
    this.companyId,
    required this.role,
    this.permissions = const [],
    required this.isActive,
    required this.isPhoneVerified,
    required this.createdAt,
    this.lastLoginAt,
  });

  /// Check if user is system admin
  bool get isSystemAdmin => role == 'system_admin';

  /// Check if user is company admin
  bool get isCompanyAdmin => role == 'company_admin';

  /// Check if user has a specific permission
  bool hasPermission(String permission) => permissions.contains(permission);
}
