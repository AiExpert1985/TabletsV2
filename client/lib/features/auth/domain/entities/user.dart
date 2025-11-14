/// User entity
class User {
  final String id;
  final String phoneNumber;
  final String? email;
  final bool isActive;
  final bool isPhoneVerified;
  final DateTime createdAt;
  final DateTime? lastLoginAt;

  User({
    required this.id,
    required this.phoneNumber,
    this.email,
    required this.isActive,
    required this.isPhoneVerified,
    required this.createdAt,
    this.lastLoginAt,
  });
}
