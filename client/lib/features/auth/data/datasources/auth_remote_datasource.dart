import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/auth/data/models/auth_response_model.dart';
import 'package:client/features/auth/data/models/token_response_model.dart';

/// Auth remote data source interface
abstract class AuthRemoteDataSource {
  /// Sign up new user
  Future<AuthResponseModel> signup(String phoneNumber, String password);

  /// Login user
  Future<AuthResponseModel> login(String phoneNumber, String password);

  /// Refresh access token
  Future<TokenResponseModel> refreshToken(String refreshToken);

  /// Logout user
  Future<void> logout(String refreshToken);

  /// Get current authenticated user
  Future<UserModel> getCurrentUser();

  /// Request password reset
  Future<void> requestPasswordReset(String phoneNumber);

  /// Reset password with token
  Future<void> resetPassword(String resetToken, String newPassword);

  /// Change password (authenticated)
  Future<void> changePassword(String oldPassword, String newPassword);
}
