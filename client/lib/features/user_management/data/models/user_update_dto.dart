/// DTO for updating an existing user
class UserUpdateDto {
  final String? name;
  final String? phoneNumber;
  final String? email;
  final String? password;
  final String? companyId;
  final String? role;
  final bool? isActive;

  UserUpdateDto({
    this.name,
    this.phoneNumber,
    this.email,
    this.password,
    this.companyId,
    this.role,
    this.isActive,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = {};

    if (name != null) json['name'] = name;
    if (phoneNumber != null) json['phone_number'] = phoneNumber;
    if (email != null) json['email'] = email;
    if (password != null) json['password'] = password;
    if (companyId != null) json['company_id'] = companyId;
    if (role != null) json['role'] = role;
    if (isActive != null) json['is_active'] = isActive;

    return json;
  }

  bool get isEmpty => toJson().isEmpty;
}
