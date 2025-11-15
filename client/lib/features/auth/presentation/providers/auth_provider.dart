import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/core/network/impl/dio_http_client.dart';
import 'package:client/core/network/interceptors/auth_interceptor.dart';
import 'package:client/core/network/interceptors/logging_interceptor.dart';
import 'package:client/core/storage/secure_token_storage.dart';
import 'package:client/features/auth/data/datasources/auth_remote_datasource_impl.dart';
import 'package:client/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:client/features/auth/domain/repositories/auth_repository.dart';
import 'package:client/features/auth/domain/services/auth_service.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';

/// Token storage provider
final tokenStorageProvider = Provider((ref) => SecureTokenStorage());

/// HTTP client provider
final httpClientProvider = Provider((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  final client = DioHttpClient();
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

/// Auth service provider
final authServiceProvider = Provider<AuthService>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthService(repository);
});

/// Auth notifier - manages auth state
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService authService;

  AuthNotifier(this.authService) : super(Initial()) {
    _checkAuthStatus();
  }

  /// Check if user is already authenticated on app start
  Future<void> _checkAuthStatus() async {
    try {
      final user = await authService.getCurrentUser();
      state = Authenticated(user);
    } catch (e) {
      state = Unauthenticated();
    }
  }

  /// Login
  Future<void> login(String phoneNumber, String password) async {
    state = Loading();
    try {
      final user = await authService.login(phoneNumber, password);
      state = Authenticated(user);
    } on HttpException catch (e) {
      state = AuthError(authService.mapErrorMessage(e));
    } catch (e) {
      state = AuthError('Login failed: ${e.toString()}');
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      await authService.logout();
      state = Unauthenticated();
    } catch (e) {
      state = Unauthenticated();
    }
  }

  /// Refresh token
  Future<void> refreshToken() async {
    try {
      final user = await authService.refreshToken();
      state = Authenticated(user);
    } catch (e) {
      state = Unauthenticated();
    }
  }

  /// Clear error state
  void clearError() {
    if (state is AuthError) {
      state = Unauthenticated();
    }
  }
}

/// Auth provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final service = ref.watch(authServiceProvider);
  return AuthNotifier(service);
});
