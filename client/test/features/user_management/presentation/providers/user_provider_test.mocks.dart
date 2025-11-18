// Manual mocks for user_provider_test.dart
import 'package:mockito/mockito.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';

class MockUserRepository extends Mock implements UserRepository {
  @override
  Future<List<User>> getUsers({int skip = 0, int limit = 100}) =>
      super.noSuchMethod(
        Invocation.method(#getUsers, [], {#skip: skip, #limit: limit}),
        returnValue: Future.value(<User>[]),
      );

  @override
  Future<User> getUserById(String id) => super.noSuchMethod(
        Invocation.method(#getUserById, [id]),
        returnValue: Future.value(
          User(
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
  Future<User> createUser(UserCreateDto dto) => super.noSuchMethod(
        Invocation.method(#createUser, [dto]),
        returnValue: Future.value(
          User(
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
  Future<User> updateUser(String id, UserUpdateDto dto) => super.noSuchMethod(
        Invocation.method(#updateUser, [id, dto]),
        returnValue: Future.value(
          User(
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
