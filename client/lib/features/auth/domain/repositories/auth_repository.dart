import 'package:client/features/auth/domain/entities/user.dart';

/// Auth repository interface
abstract class AuthRepository {
  /// Sign up new user
  Future<User> signup(String phoneNumber, String password);

  /// Login user
  Future<User> login(String phoneNumber, String password);

  /// Refresh access token
  Future<User> refreshToken();

  /// Logout user
  Future<void> logout();

  /// Get current authenticated user
  Future<User> getCurrentUser();
}
