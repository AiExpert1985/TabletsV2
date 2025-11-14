import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/core/network/impl/dio_http_client.dart';
import 'package:client/core/network/interceptors/auth_interceptor.dart';
import 'package:client/core/network/interceptors/logging_interceptor.dart';
import 'package:client/core/storage/secure_token_storage.dart';
import 'package:client/features/auth/data/datasources/auth_remote_datasource_impl.dart';
import 'package:client/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:client/features/auth/domain/repositories/auth_repository.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';

/// Token storage provider
final tokenStorageProvider = Provider((ref) => SecureTokenStorage());

/// HTTP client provider
final httpClientProvider = Provider((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  final client = DioHttpClient();

  // Add interceptors
  client.addInterceptor(AuthInterceptor(tokenStorage));
  client.addInterceptor(LoggingInterceptor());

  return client;
});

/// Auth repository provider
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final httpClient = ref.watch(httpClientProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);

  return AuthRepositoryImpl(
    remoteDataSource: AuthRemoteDataSourceImpl(httpClient),
    tokenStorage: tokenStorage,
  );
});

/// Auth notifier - manages auth state
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository authRepository;

  AuthNotifier(this.authRepository) : super(Initial()) {
    _checkAuthStatus();
  }

  /// Check if user is already authenticated on app start
  Future<void> _checkAuthStatus() async {
    try {
      final user = await authRepository.getCurrentUser();
      state = Authenticated(user);
    } catch (e) {
      state = Unauthenticated();
    }
  }

  /// Sign up
  Future<void> signup(String phoneNumber, String password) async {
    state = Loading();
    try {
      final user = await authRepository.signup(phoneNumber, password);
      state = Authenticated(user);
    } on HttpException catch (e) {
      state = AuthError(_mapErrorMessage(e));
    } catch (e) {
      state = AuthError('Signup failed: ${e.toString()}');
    }
  }

  /// Login
  Future<void> login(String phoneNumber, String password) async {
    state = Loading();
    try {
      final user = await authRepository.login(phoneNumber, password);
      state = Authenticated(user);
    } on HttpException catch (e) {
      state = AuthError(_mapErrorMessage(e));
    } catch (e) {
      state = AuthError('Login failed: ${e.toString()}');
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      await authRepository.logout();
      state = Unauthenticated();
    } catch (e) {
      // Clear state anyway
      state = Unauthenticated();
    }
  }

  /// Refresh token
  Future<void> refreshToken() async {
    try {
      final user = await authRepository.refreshToken();
      state = Authenticated(user);
    } catch (e) {
      state = Unauthenticated();
    }
  }

  /// Request password reset
  Future<void> requestPasswordReset(String phoneNumber) async {
    try {
      await authRepository.requestPasswordReset(phoneNumber);
    } on HttpException catch (e) {
      throw _mapErrorMessage(e);
    }
  }

  /// Reset password
  Future<void> resetPassword(String resetToken, String newPassword) async {
    try {
      await authRepository.resetPassword(resetToken, newPassword);
    } on HttpException catch (e) {
      throw _mapErrorMessage(e);
    }
  }

  /// Change password
  Future<void> changePassword(String oldPassword, String newPassword) async {
    try {
      await authRepository.changePassword(oldPassword, newPassword);
      // Force re-login after password change
      state = Unauthenticated();
    } on HttpException catch (e) {
      throw _mapErrorMessage(e);
    }
  }

  /// Clear error state
  void clearError() {
    if (state is AuthError) {
      state = Unauthenticated();
    }
  }

  /// Map HTTP exception to user-friendly message
  String _mapErrorMessage(HttpException e) {
    if (e.code == 'PHONE_ALREADY_EXISTS') {
      return 'Phone number already registered';
    } else if (e.code == 'INVALID_CREDENTIALS') {
      return 'Invalid phone number or password';
    } else if (e.code == 'ACCOUNT_DEACTIVATED') {
      return 'Account has been deactivated';
    } else if (e.code == 'PASSWORD_TOO_WEAK') {
      return e.message;
    } else if (e.code == 'RATE_LIMIT_EXCEEDED') {
      return e.message;
    } else if (e is NetworkException) {
      return 'No internet connection';
    } else if (e is TimeoutException) {
      return 'Request timeout. Please try again.';
    } else if (e is UnauthorizedException) {
      return 'Session expired. Please login again.';
    } else {
      return e.message;
    }
  }
}

/// Auth provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});
