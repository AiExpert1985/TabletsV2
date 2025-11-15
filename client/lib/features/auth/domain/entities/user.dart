/// User entity
class User {
  final String id;
  final String phoneNumber;
  final String? email;
  final String? companyId;  // NULL for system admin
  final String role;  // system_admin, company_admin, user
  final List<String> companyRoles;  // e.g., ["accountant", "sales"]
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
    this.companyRoles = const [],
    this.permissions = const [],
    required this.isActive,
    required this.isPhoneVerified,
    required this.createdAt,
    this.lastLoginAt,
  });

  /// Check if user is system admin
  bool get isSystemAdmin => role == 'system_admin';

  /// Check if user has a specific permission
  bool hasPermission(String permission) => permissions.contains(permission);
}
