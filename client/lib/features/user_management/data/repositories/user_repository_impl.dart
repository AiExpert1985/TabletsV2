import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/data/datasources/user_remote_datasource.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';

/// User management repository implementation
class UserRepositoryImpl implements UserRepository {
  final UserRemoteDataSource remoteDataSource;

  UserRepositoryImpl({required this.remoteDataSource});

  @override
  Future<List<User>> getUsers({int skip = 0, int limit = 100}) async {
    try {
      final users = await remoteDataSource.getUsers(skip: skip, limit: limit);
      return users.map((u) => u.toEntity()).toList();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> getUserById(String id) async {
    try {
      final user = await remoteDataSource.getUserById(id);
      return user.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> createUser(UserCreateDto dto) async {
    try {
      final user = await remoteDataSource.createUser(dto);
      return user.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<User> updateUser(String id, UserUpdateDto dto) async {
    try {
      final user = await remoteDataSource.updateUser(id, dto);
      return user.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<void> deleteUser(String id) async {
    try {
      await remoteDataSource.deleteUser(id);
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }
}
