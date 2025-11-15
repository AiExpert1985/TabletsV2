import 'package:client/core/network/http_exception.dart';
import 'package:client/core/utils/validators.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/repositories/auth_repository.dart';

/// Auth service - handles business logic and validation
class AuthService {
  final AuthRepository repository;

  AuthService(this.repository);

  /// Login with validation and normalization
  Future<User> login(String phoneNumber, String password) async {
    final normalized = PhoneValidator.normalize(phoneNumber);
    return await repository.login(normalized, password);
  }

  /// Signup with validation and normalization
  Future<User> signup(String phoneNumber, String password) async {
    final normalized = PhoneValidator.normalize(phoneNumber);
    return await repository.signup(normalized, password);
  }

  /// Logout current session
  Future<void> logout() async {
    await repository.logout();
  }

  /// Refresh authentication token
  Future<User> refreshToken() async {
    return await repository.refreshToken();
  }

  /// Get current authenticated user
  Future<User> getCurrentUser() async {
    return await repository.getCurrentUser();
  }

  /// Map HTTP exception to user-friendly error message
  String mapErrorMessage(HttpException e) {
    if (e.code == 'INVALID_CREDENTIALS') {
      return 'Invalid phone number or password';
    }
    if (e.code == 'ACCOUNT_DEACTIVATED') {
      return 'Account has been deactivated';
    }
    if (e.code == 'RATE_LIMIT_EXCEEDED') {
      return e.message;
    }
    if (e is NetworkException) {
      return 'No internet connection';
    }
    if (e is TimeoutException) {
      return 'Request timeout. Please try again.';
    }
    if (e is UnauthorizedException) {
      return 'Session expired. Please login again.';
    }
    return e.message;
  }
}
