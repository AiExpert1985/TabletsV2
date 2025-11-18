/// DTO for creating a new user
class UserCreateDto {
  final String phoneNumber;
  final String password;
  final String? email;
  final String? companyId;
  final String role;
  final bool isActive;

  UserCreateDto({
    required this.phoneNumber,
    required this.password,
    this.email,
    this.companyId,
    this.role = 'viewer',
    this.isActive = true,
  });

  Map<String, dynamic> toJson() {
    return {
      'phone_number': phoneNumber,
      'password': password,
      if (email != null) 'email': email,
      if (companyId != null) 'company_id': companyId,
      'role': role,
      'is_active': isActive,
    };
  }
}
