// Manual mocks for user_repository_impl_test.dart
import 'package:mockito/mockito.dart';
import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/user_management/data/datasources/user_remote_datasource.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';

class MockUserRemoteDataSource extends Mock implements UserRemoteDataSource {
  @override
  Future<List<UserModel>> getUsers({int skip = 0, int limit = 100}) =>
      super.noSuchMethod(
        Invocation.method(#getUsers, [], {#skip: skip, #limit: limit}),
        returnValue: Future.value(<UserModel>[]),
      );

  @override
  Future<UserModel> getUserById(String id) => super.noSuchMethod(
        Invocation.method(#getUserById, [id]),
        returnValue: Future.value(
          UserModel(
            id: '1',
            phoneNumber: '+9647701234567',
            role: 'viewer',
            isActive: true,
            isPhoneVerified: true,
            createdAt: DateTime.now(),
          ),
        ),
      );

  @override
  Future<UserModel> createUser(UserCreateDto dto) => super.noSuchMethod(
        Invocation.method(#createUser, [dto]),
        returnValue: Future.value(
          UserModel(
            id: '1',
            phoneNumber: '+9647701234567',
            role: 'viewer',
            isActive: true,
            isPhoneVerified: true,
            createdAt: DateTime.now(),
          ),
        ),
      );

  @override
  Future<UserModel> updateUser(String id, UserUpdateDto dto) =>
      super.noSuchMethod(
        Invocation.method(#updateUser, [id, dto]),
        returnValue: Future.value(
          UserModel(
            id: '1',
            phoneNumber: '+9647701234567',
            role: 'viewer',
            isActive: true,
            isPhoneVerified: true,
            createdAt: DateTime.now(),
          ),
        ),
      );

  @override
  Future<void> deleteUser(String id) => super.noSuchMethod(
        Invocation.method(#deleteUser, [id]),
        returnValue: Future.value(),
      );
}
