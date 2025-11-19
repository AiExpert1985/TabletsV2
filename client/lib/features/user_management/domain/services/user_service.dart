import 'package:client/core/network/http_exception.dart';
import 'package:client/core/utils/validators.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';

/// User service - handles business logic and validation for user management
class UserService {
  final UserRepository repository;

  UserService(this.repository);

  /// Get all users with pagination (system admin only)
  Future<List<User>> getUsers({int skip = 0, int limit = 100}) async {
    return await repository.getUsers(skip: skip, limit: limit);
  }

  /// Get user by ID (system admin only)
  Future<User> getUserById(String id) async {
    return await repository.getUserById(id);
  }

  /// Create a new user with validation and normalization
  Future<User> createUser({
    required String name,
    required String phoneNumber,
    required String password,
    String? email,
    String? companyId,
    String role = 'viewer',
    bool isActive = true,
  }) async {
    // Normalize phone number before creating user
    final normalizedPhone = PhoneValidator.normalize(phoneNumber);

    final dto = UserCreateDto(
      name: name,
      phoneNumber: normalizedPhone,
      password: password,
      email: email,
      companyId: companyId,
      role: role,
      isActive: isActive,
    );

    return await repository.createUser(dto);
  }

  /// Update user with validation and normalization
  Future<User> updateUser({
    required String id,
    String? name,
    String? phoneNumber,
    String? email,
    String? password,
    String? companyId,
    String? role,
    bool? isActive,
  }) async {
    // Normalize phone number if provided
    final normalizedPhone = phoneNumber != null
        ? PhoneValidator.normalize(phoneNumber)
        : null;

    final dto = UserUpdateDto(
      name: name,
      phoneNumber: normalizedPhone,
      email: email,
      password: password,
      companyId: companyId,
      role: role,
      isActive: isActive,
    );

    if (dto.isEmpty) {
      throw Exception('No fields to update');
    }

    return await repository.updateUser(id, dto);
  }

  /// Delete user (system admin only)
  Future<void> deleteUser(String id) async {
    await repository.deleteUser(id);
  }

  /// Map HTTP exception to user-friendly error message
  String mapErrorMessage(HttpException e) {
    if (e.code == 'USER_NOT_FOUND') {
      return 'User not found';
    }
    if (e.code == 'DUPLICATE_PHONE') {
      return 'Phone number already exists';
    }
    if (e.code == 'INVALID_ROLE') {
      return 'Invalid role specified';
    }
    if (e.code == 'INVALID_COMPANY') {
      return 'Invalid company specified';
    }
    if (e is NetworkException) {
      return 'No internet connection';
    }
    if (e is TimeoutException) {
      return 'Request timeout. Please try again.';
    }
    if (e is UnauthorizedException) {
      return 'You do not have permission to perform this action';
    }
    return e.message;
  }
}
