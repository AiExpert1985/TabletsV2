import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';

/// User management repository interface
abstract class UserRepository {
  /// Get all users (system admin only)
  Future<List<User>> getUsers({int skip = 0, int limit = 100});

  /// Get user by ID (system admin only)
  Future<User> getUserById(String id);

  /// Create a new user (system admin only)
  Future<User> createUser(UserCreateDto dto);

  /// Update user (system admin only)
  Future<User> updateUser(String id, UserUpdateDto dto);

  /// Delete user (system admin only)
  Future<void> deleteUser(String id);
}
