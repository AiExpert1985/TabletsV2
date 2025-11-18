import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/http_client.dart';
import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';

/// User management remote data source
class UserRemoteDataSource {
  final HttpClient httpClient;

  UserRemoteDataSource(this.httpClient);

  /// Get all users (system admin only)
  Future<List<UserModel>> getUsers({int skip = 0, int limit = 100}) async {
    final response = await httpClient.get(
      AppConfig.usersEndpoint,
      queryParameters: {
        'skip': skip,
        'limit': limit,
      },
    );

    final List<dynamic> data = response.data as List<dynamic>;
    return data.map((json) => UserModel.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Get user by ID (system admin only)
  Future<UserModel> getUserById(String id) async {
    final response = await httpClient.get(
      '${AppConfig.usersEndpoint}/$id',
    );

    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Create a new user (system admin only)
  Future<UserModel> createUser(UserCreateDto dto) async {
    final response = await httpClient.post(
      AppConfig.usersEndpoint,
      data: dto.toJson(),
    );

    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Update user (system admin only)
  Future<UserModel> updateUser(String id, UserUpdateDto dto) async {
    final response = await httpClient.put(
      '${AppConfig.usersEndpoint}/$id',
      data: dto.toJson(),
    );

    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Delete user (system admin only)
  Future<void> deleteUser(String id) async {
    await httpClient.delete('${AppConfig.usersEndpoint}/$id');
  }
}
