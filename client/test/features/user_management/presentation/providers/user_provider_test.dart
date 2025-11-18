import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/presentation/providers/user_provider.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';

import 'user_provider_test.mocks.dart';

void main() {
  group('UserNotifier', () {
    late UserNotifier notifier;
    late MockUserRepository mockRepository;

    // Register fallback values for custom types
    setUpAll(() {
      registerFallbackValue(UserCreateDto(
        phoneNumber: '',
        password: '',
      ));
      registerFallbackValue(UserUpdateDto());
    });

    setUp(() {
      mockRepository = MockUserRepository();
      notifier = UserNotifier(mockRepository);
    });

    final testDateTime = DateTime.parse('2024-01-15T10:30:00.000Z');
    final testUser1 = User(
      id: '1',
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
      test('emits loading then loaded state on success', () async {
        final users = [testUser1, testUser2];
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => users);

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.getUsers();

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UsersLoaded>());
        expect((states[1] as UsersLoaded).users, hasLength(2));
      });

      test('emits loading then error state on HttpException', () async {
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenThrow(HttpException(message: 'Network error'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.getUsers();

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
        expect((states[1] as UserError).message, 'Network error');
      });

      test('emits loading then error state on generic exception', () async {
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenThrow(Exception('Unknown error'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.getUsers();

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
        expect((states[1] as UserError).message, contains('Failed to load users'));
      });

      test('passes skip and limit parameters', () async {
        when(mockRepository.getUsers(skip: 10, limit: 50))
            .thenAnswer((_) async => []);

        await notifier.getUsers(skip: 10, limit: 50);

        verify(mockRepository.getUsers(skip: 10, limit: 50)).called(1);
      });
    });

    group('getUserById', () {
      test('emits loading then loaded state on success', () async {
        when(mockRepository.getUserById('1'))
            .thenAnswer((_) async => testUser1);

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.getUserById('1');

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserLoaded>());
        expect((states[1] as UserLoaded).user.id, '1');
      });

      test('emits error state on failure', () async {
        when(mockRepository.getUserById('1'))
            .thenThrow(HttpException(message: 'User not found'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.getUserById('1');

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
      });
    });

    group('createUser', () {
      test('emits loading then created state on success', () async {
        when(mockRepository.createUser(any))
            .thenAnswer((_) async => testUser1);

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test1@example.com',
          companyId: 'company-1',
          role: 'salesperson',
        );

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserCreated>());
        expect((states[1] as UserCreated).user.phoneNumber, '+9647701234567');
      });

      test('emits error state on conflict', () async {
        when(mockRepository.createUser(any))
            .thenThrow(HttpException(message: 'Phone number already exists'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
        );

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
        expect((states[1] as UserError).message, 'Phone number already exists');
      });

      test('creates user with optional fields', () async {
        when(mockRepository.createUser(any))
            .thenAnswer((_) async => testUser1);

        await notifier.createUser(
          phoneNumber: '+9647701234567',
          password: 'password123',
          email: 'test@example.com',
          companyId: 'company-1',
          role: 'accountant',
          isActive: false,
        );

        verify(mockRepository.createUser(any)).called(1);
      });
    });

    group('updateUser', () {
      test('emits loading then updated state on success', () async {
        when(mockRepository.updateUser(any, any))
            .thenAnswer((_) async => testUser1);

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.updateUser(
          id: '1',
          phoneNumber: '+9647701234567',
          email: 'updated@example.com',
        );

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserUpdated>());
      });

      test('emits error state when no fields provided', () async {
        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.updateUser(id: '1');

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
        expect((states[1] as UserError).message, 'No fields to update');
      });

      test('emits error state on failure', () async {
        when(mockRepository.updateUser(any, any))
            .thenThrow(HttpException(message: 'User not found'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.updateUser(
          id: '1',
          phoneNumber: '+9647701234568',
        );

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
      });
    });

    group('deleteUser', () {
      test('emits loading then deleted state on success', () async {
        when(mockRepository.deleteUser('1'))
            .thenAnswer((_) async => {});

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.deleteUser('1');

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserDeleted>());
      });

      test('emits error state on failure', () async {
        when(mockRepository.deleteUser('1'))
            .thenThrow(HttpException(message: 'Cannot delete yourself'));

        final states = <UserState>[];
        notifier.addListener((state) => states.add(state));

        await notifier.deleteUser('1');

        expect(states[0], isA<UserLoading>());
        expect(states[1], isA<UserError>());
        expect((states[1] as UserError).message, 'Cannot delete yourself');
      });
    });

    group('reset', () {
      test('resets state to initial', () async {
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => [testUser1]);

        await notifier.getUsers();
        expect(notifier.state, isA<UsersLoaded>());

        notifier.reset();
        expect(notifier.state, isA<UserInitial>());
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenThrow(HttpException(message: 'Error'));

        await notifier.getUsers();
        expect(notifier.state, isA<UserError>());

        notifier.clearError();
        expect(notifier.state, isA<UserInitial>());
      });

      test('does not change non-error state', () async {
        when(mockRepository.getUsers(skip: 0, limit: 100))
            .thenAnswer((_) async => [testUser1]);

        await notifier.getUsers();
        expect(notifier.state, isA<UsersLoaded>());

        notifier.clearError();
        expect(notifier.state, isA<UsersLoaded>());
      });
    });
  });
}
