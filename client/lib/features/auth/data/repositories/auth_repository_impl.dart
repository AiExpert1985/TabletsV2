import 'package:client/core/network/http_exception.dart';
import 'package:client/core/storage/token_storage.dart';
import 'package:client/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/repositories/auth_repository.dart';

/// Auth repository implementation - pure data access
class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final TokenStorage tokenStorage;

  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.tokenStorage,
  });

  @override
  Future<User> signup(String phoneNumber, String password) async {
    try {
      final response = await remoteDataSource.signup(phoneNumber, password);
      await tokenStorage.saveAccessToken(response.tokens.accessToken);
      await tokenStorage.saveRefreshToken(response.tokens.refreshToken);
      return response.user.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> login(String phoneNumber, String password) async {
    try {
      final response = await remoteDataSource.login(phoneNumber, password);
      await tokenStorage.saveAccessToken(response.tokens.accessToken);
      await tokenStorage.saveRefreshToken(response.tokens.refreshToken);
      return response.user.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> refreshToken() async {
    try {
      // Get refresh token from storage
      final refreshToken = await tokenStorage.getRefreshToken();
      if (refreshToken == null) {
        throw UnauthorizedException();
      }

      // Call API
      final response = await remoteDataSource.refreshToken(refreshToken);

      // Store new tokens
      await tokenStorage.saveAccessToken(response.accessToken);
      await tokenStorage.saveRefreshToken(response.refreshToken);

      // Get current user
      return await getCurrentUser();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<void> logout() async {
    try {
      // Get refresh token
      final refreshToken = await tokenStorage.getRefreshToken();

      // Call API (fail silently if error)
      if (refreshToken != null) {
        try {
          await remoteDataSource.logout(refreshToken);
        } catch (e) {
          // Ignore errors - clear tokens anyway
        }
      }

      // Clear tokens from storage
      await tokenStorage.clearTokens();
    } catch (e) {
      // Always clear tokens even if API call fails
      await tokenStorage.clearTokens();
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> getCurrentUser() async {
    try {
      final userModel = await remoteDataSource.getCurrentUser();
      return userModel.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }
}
