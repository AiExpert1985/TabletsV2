import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/domain/services/user_service.dart';
import 'package:client/features/user_management/presentation/providers/user_provider.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';

import 'user_provider_test.mocks.dart';

@GenerateMocks([UserService])
void main() {
  group('UserNotifier', () {
    late UserNotifier notifier;
    late MockUserService mockService;

    setUp(() {
      mockService = MockUserService();
      notifier = UserNotifier(mockService);
    });

    final testDateTime = DateTime.parse('2024-01-15T10:30:00.000Z');
    final testUser1 = User(
      id: '1',
      name: 'Test User',
      phoneNumber: '+9647701234567',
      email: 'test1@example.com',
      companyId: 'company-1',
      role: 'salesperson',
      isActive: true,
      isPhoneVerified: true,
      createdAt: testDateTime,
    );

    final testUser2 = User(
      id: '2',
      name: 'Test User',
      phoneNumber: '+9647701234568',
      email: 'test2@example.com',
      companyId: 'company-1',
      role: 'viewer',
      isActive: true,
      isPhoneVerified: true,
      createdAt: testDateTime,
    );

    group('initial state', () {
      test('is UserInitial', () {
        expect(notifier.state, isA<UserInitial>());
      });
    });

    group('getUsers', () {
      test('emits loaded state on success', () async {
        final users = [testUser1, testUser2];
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => users);

        await notifier.getUsers();

        expect(notifier.state, isA<UsersLoaded>());
        expect((notifier.state as UsersLoaded).users, hasLength(2));
      });

      test('emits error state on HttpException', () async {
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenThrow(HttpException(message: 'Network error'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('Network error');

        await notifier.getUsers();

        expect(notifier.state, isA<UserError>());
        expect((notifier.state as UserError).message, 'Network error');
      });

      test('emits error state on generic exception', () async {
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenThrow(Exception('Unknown error'));

        await notifier.getUsers();

        expect(notifier.state, isA<UserError>());
        expect((notifier.state as UserError).message, contains('Failed to load users'));
      });

      test('passes skip and limit parameters', () async {
        when(mockService.getUsers(skip: 10, limit: 50))
            .thenAnswer((_) async => []);

        await notifier.getUsers(skip: 10, limit: 50);

        verify(mockService.getUsers(skip: 10, limit: 50)).called(1);
      });
    });

    group('getUserById', () {
      test('emits loaded state on success', () async {
        when(mockService.getUserById('1'))
            .thenAnswer((_) async => testUser1);

        await notifier.getUserById('1');

        expect(notifier.state, isA<UserLoaded>());
        expect((notifier.state as UserLoaded).user.id, '1');
      });

      test('emits error state on failure', () async {
        when(mockService.getUserById('1'))
            .thenThrow(HttpException(message: 'User not found'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('User not found');

        await notifier.getUserById('1');

        expect(notifier.state, isA<UserError>());
      });
    });

    group('createUser', () {
      test('emits created state on success', () async {
        when(mockService.createUser(
          phoneNumber: anyNamed('phoneNumber'),
          password: anyNamed('password'),
          email: anyNamed('email'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenAnswer((_) async => testUser1);

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test1@example.com',
          companyId: 'company-1',
          role: 'salesperson',
        );

        expect(notifier.state, isA<UserCreated>());
        expect((notifier.state as UserCreated).user.phoneNumber, '+9647701234567');
      });

      test('emits error state on conflict', () async {
        when(mockService.createUser(
          phoneNumber: anyNamed('phoneNumber'),
          password: anyNamed('password'),
          email: anyNamed('email'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenThrow(HttpException(message: 'Phone number already exists'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('Phone number already exists');

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
        );

        expect(notifier.state, isA<UserError>());
        expect((notifier.state as UserError).message, 'Phone number already exists');
      });

      test('creates user with optional fields', () async {
        when(mockService.createUser(
          phoneNumber: anyNamed('phoneNumber'),
          password: anyNamed('password'),
          email: anyNamed('email'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenAnswer((_) async => testUser1);

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test@example.com',
          companyId: 'company-1',
          role: 'accountant',
          isActive: false,
        );

        verify(mockService.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test@example.com',
          companyId: 'company-1',
          role: 'accountant',
          isActive: false,
        )).called(1);
      });
    });

    group('updateUser', () {
      test('emits updated state on success', () async {
        when(mockService.updateUser(
          id: anyNamed('id'),
          phoneNumber: anyNamed('phoneNumber'),
          email: anyNamed('email'),
          password: anyNamed('password'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenAnswer((_) async => testUser1);

        await notifier.updateUser(
          id: '1',
          name: 'Test User',
          phoneNumber: '+9647701234567',
          email: 'updated@example.com',
        );

        expect(notifier.state, isA<UserUpdated>());
      });

      test('emits error state when no fields provided', () async {
        when(mockService.updateUser(
          id: anyNamed('id'),
          phoneNumber: anyNamed('phoneNumber'),
          email: anyNamed('email'),
          password: anyNamed('password'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenThrow(Exception('No fields to update'));

        await notifier.updateUser(id: '1');

        expect(notifier.state, isA<UserError>());
        expect((notifier.state as UserError).message, contains('No fields to update'));
      });

      test('emits error state on failure', () async {
        when(mockService.updateUser(
          id: anyNamed('id'),
          phoneNumber: anyNamed('phoneNumber'),
          email: anyNamed('email'),
          password: anyNamed('password'),
          companyId: anyNamed('companyId'),
          role: anyNamed('role'),
          isActive: anyNamed('isActive'),
        )).thenThrow(HttpException(message: 'User not found'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('User not found');

        await notifier.updateUser(
          id: '1',
          name: 'Test User',
          phoneNumber: '+9647701234568',
        );

        expect(notifier.state, isA<UserError>());
      });
    });

    group('deleteUser', () {
      test('emits deleted state on success', () async {
        when(mockService.deleteUser('1'))
            .thenAnswer((_) async => {});

        await notifier.deleteUser('1');

        expect(notifier.state, isA<UserDeleted>());
      });

      test('emits error state on failure', () async {
        when(mockService.deleteUser('1'))
            .thenThrow(HttpException(message: 'Cannot delete yourself'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('Cannot delete yourself');

        await notifier.deleteUser('1');

        expect(notifier.state, isA<UserError>());
        expect((notifier.state as UserError).message, 'Cannot delete yourself');
      });
    });

    group('reset', () {
      test('resets state to initial', () async {
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => [testUser1]);

        await notifier.getUsers();
        expect(notifier.state, isA<UsersLoaded>());

        notifier.reset();
        expect(notifier.state, isA<UserInitial>());
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenThrow(HttpException(message: 'Error'));
        when(mockService.mapErrorMessage(any))
            .thenReturn('Error');

        await notifier.getUsers();
        expect(notifier.state, isA<UserError>());

        notifier.clearError();
        expect(notifier.state, isA<UserInitial>());
      });

      test('does not change non-error state', () async {
        when(mockService.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => [testUser1]);

        await notifier.getUsers();
        expect(notifier.state, isA<UsersLoaded>());

        notifier.clearError();
        expect(notifier.state, isA<UsersLoaded>());
      });
    });
  });
}
