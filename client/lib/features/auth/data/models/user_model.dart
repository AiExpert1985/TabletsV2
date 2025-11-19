import 'package:client/features/auth/domain/entities/user.dart';

/// User model - JSON serialization
class UserModel extends User {
  UserModel({
    required super.id,
    required super.name,
    required super.phoneNumber,
    super.email,
    super.companyId,
    required super.role,
    super.permissions = const [],
    required super.isActive,
    required super.isPhoneVerified,
    required super.createdAt,
    super.lastLoginAt,
  });

  /// From JSON
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      name: json['name'] as String,
      phoneNumber: json['phone_number'] as String,
      email: json['email'] as String?,
      companyId: json['company_id'] as String?,
      role: json['role'] as String,
      permissions: (json['permissions'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      isActive: json['is_active'] as bool,
      isPhoneVerified: json['is_phone_verified'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      lastLoginAt: json['last_login_at'] != null
          ? DateTime.parse(json['last_login_at'] as String)
          : null,
    );
  }

  /// To JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'phone_number': phoneNumber,
      'email': email,
      'company_id': companyId,
      'role': role,
      'permissions': permissions,
      'is_active': isActive,
      'is_phone_verified': isPhoneVerified,
      'created_at': createdAt.toIso8601String(),
      'last_login_at': lastLoginAt?.toIso8601String(),
    };
  }

  /// Convert to entity
  User toEntity() => this;
}
