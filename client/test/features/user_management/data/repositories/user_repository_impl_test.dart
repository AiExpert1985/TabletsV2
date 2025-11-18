import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/data/repositories/user_repository_impl.dart';

import 'user_repository_impl_test.mocks.dart';

void main() {
  group('UserRepositoryImpl', () {
    late UserRepositoryImpl repository;
    late MockUserRemoteDataSource mockDataSource;

    setUp(() {
      mockDataSource = MockUserRemoteDataSource();
      repository = UserRepositoryImpl(remoteDataSource: mockDataSource);
    });

    final testDateTime = DateTime.parse('2024-01-15T10:30:00.000Z');
    final testUserModel = UserModel(
      id: '1',
      phoneNumber: '+9647701234567',
      email: 'test@example.com',
      companyId: 'company-1',
      role: 'salesperson',
      isActive: true,
      isPhoneVerified: true,
      createdAt: testDateTime,
    );

    group('getUsers', () {
      test('returns list of users on success', () async {
        final users = [testUserModel];
        when(mockDataSource.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => users);

        final result = await repository.getUsers();

        expect(result, hasLength(1));
        expect(result[0].id, '1');
        expect(result[0].phoneNumber, '+9647701234567');
        verify(mockDataSource.getUsers(skip: 0, limit: 100)).called(1);
      });

      test('passes skip and limit parameters', () async {
        when(mockDataSource.getUsers(skip: 10, limit: 50))
            .thenAnswer((_) async => []);

        await repository.getUsers(skip: 10, limit: 50);

        verify(mockDataSource.getUsers(skip: 10, limit: 50)).called(1);
      });

      test('rethrows HttpException', () async {
        when(mockDataSource.getUsers(skip: 0, limit: 100))
            .thenThrow(HttpException(message: 'Network error'));

        expect(
          () => repository.getUsers(),
          throwsA(isA<HttpException>()),
        );
      });

      test('wraps other exceptions in HttpException', () async {
        when(mockDataSource.getUsers(skip: 0, limit: 100))
            .thenThrow(Exception('Unknown error'));

        expect(
          () => repository.getUsers(),
          throwsA(isA<HttpException>()),
        );
      });
    });

    group('getUserById', () {
      test('returns user on success', () async {
        when(mockDataSource.getUserById('1'))
            .thenAnswer((_) async => testUserModel);

        final result = await repository.getUserById('1');

        expect(result.id, '1');
        expect(result.phoneNumber, '+9647701234567');
        verify(mockDataSource.getUserById('1')).called(1);
      });

      test('rethrows HttpException', () async {
        when(mockDataSource.getUserById('1'))
            .thenThrow(HttpException(message: 'User not found'));

        expect(
          () => repository.getUserById('1'),
          throwsA(isA<HttpException>()),
        );
      });
    });

    group('createUser', () {
      test('returns created user on success', () async {
        final dto = UserCreateDto(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test@example.com',
          companyId: 'company-1',
          role: 'salesperson',
          isActive: true,
        );

        when(mockDataSource.createUser(dto))
            .thenAnswer((_) async => testUserModel);

        final result = await repository.createUser(dto);

        expect(result.id, '1');
        expect(result.phoneNumber, '+9647701234567');
        verify(mockDataSource.createUser(dto)).called(1);
      });

      test('rethrows HttpException on conflict', () async {
        final dto = UserCreateDto(
          phoneNumber: '+9647701234567',
          password: 'password123',
          role: 'viewer',
        );

        when(mockDataSource.createUser(dto))
            .thenThrow(HttpException(message: 'Phone number already exists'));

        expect(
          () => repository.createUser(dto),
          throwsA(isA<HttpException>()),
        );
      });
    });

    group('updateUser', () {
      test('returns updated user on success', () async {
        final dto = UserUpdateDto(
          phoneNumber: '+9647701234568',
          email: 'updated@example.com',
        );

        final updatedUser = UserModel(
          id: '1',
          phoneNumber: '+9647701234568',
          email: 'updated@example.com',
          companyId: 'company-1',
          role: 'salesperson',
          isActive: true,
          isPhoneVerified: true,
          createdAt: testDateTime,
        );

        when(mockDataSource.updateUser('1', dto))
            .thenAnswer((_) async => updatedUser);

        final result = await repository.updateUser('1', dto);

        expect(result.phoneNumber, '+9647701234568');
        expect(result.email, 'updated@example.com');
        verify(mockDataSource.updateUser('1', dto)).called(1);
      });

      test('rethrows HttpException', () async {
        final dto = UserUpdateDto(phoneNumber: '+9647701234568');

        when(mockDataSource.updateUser('1', dto))
            .thenThrow(HttpException(message: 'User not found'));

        expect(
          () => repository.updateUser('1', dto),
          throwsA(isA<HttpException>()),
        );
      });
    });

    group('deleteUser', () {
      test('completes successfully', () async {
        when(mockDataSource.deleteUser('1'))
            .thenAnswer((_) async => {});

        await repository.deleteUser('1');

        verify(mockDataSource.deleteUser('1')).called(1);
      });

      test('rethrows HttpException', () async {
        when(mockDataSource.deleteUser('1'))
            .thenThrow(HttpException(message: 'Cannot delete yourself'));

        expect(
          () => repository.deleteUser('1'),
          throwsA(isA<HttpException>()),
        );
      });
    });
  });
}
