import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/http_client.dart';
import 'package:client/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:client/features/auth/data/models/auth_response_model.dart';
import 'package:client/features/auth/data/models/token_response_model.dart';
import 'package:client/features/auth/data/models/user_model.dart';

/// Auth remote data source implementation
class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final HttpClient httpClient;

  AuthRemoteDataSourceImpl(this.httpClient);

  @override
  Future<AuthResponseModel> signup(String phoneNumber, String password) async {
    final response = await httpClient.post(
      '${AppConfig.authEndpoint}/signup',
      data: {
        'phone_number': phoneNumber,
        'password': password,
        'password_confirm': password,
      },
    );

    return AuthResponseModel.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<AuthResponseModel> login(String phoneNumber, String password) async {
    final response = await httpClient.post(
      '${AppConfig.authEndpoint}/login',
      data: {
        'phone_number': phoneNumber,
        'password': password,
      },
    );

    return AuthResponseModel.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<TokenResponseModel> refreshToken(String refreshToken) async {
    final response = await httpClient.post(
      '${AppConfig.authEndpoint}/refresh',
      data: {
        'refresh_token': refreshToken,
      },
    );

    return TokenResponseModel.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<void> logout(String refreshToken) async {
    await httpClient.post(
      '${AppConfig.authEndpoint}/logout',
      data: {
        'refresh_token': refreshToken,
      },
    );
  }

  @override
  Future<UserModel> getCurrentUser() async {
    final response = await httpClient.get(
      '${AppConfig.authEndpoint}/me',
    );

    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<void> requestPasswordReset(String phoneNumber) async {
    await httpClient.post(
      '${AppConfig.authEndpoint}/password/request-reset',
      data: {
        'phone_number': phoneNumber,
      },
    );
  }

  @override
  Future<void> resetPassword(String resetToken, String newPassword) async {
    await httpClient.post(
      '${AppConfig.authEndpoint}/password/reset',
      data: {
        'reset_token': resetToken,
        'new_password': newPassword,
        'new_password_confirm': newPassword,
      },
    );
  }

  @override
  Future<void> changePassword(String oldPassword, String newPassword) async {
    await httpClient.post(
      '${AppConfig.authEndpoint}/password/change',
      data: {
        'old_password': oldPassword,
        'new_password': newPassword,
        'new_password_confirm': newPassword,
      },
    );
  }
}
