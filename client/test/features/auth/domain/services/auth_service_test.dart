import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:client/features/auth/domain/services/auth_service.dart';
import 'package:client/features/auth/domain/repositories/auth_repository.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/core/network/http_exception.dart';

import 'auth_service_test.mocks.dart';

// Generate mocks
@GenerateMocks([AuthRepository])
void main() {
  late AuthService authService;
  late MockAuthRepository mockRepository;

  setUp(() {
    mockRepository = MockAuthRepository();
    authService = AuthService(mockRepository);
  });

  group('AuthService', () {
    final testUser = User(
      id: '123e4567-e89b-12d3-a456-426614174000',
      phoneNumber: '9647701234567',
      email: 'test@example.com',
      companyId: '223e4567-e89b-12d3-a456-426614174000',
      role: 'user',
      isActive: true,
      isPhoneVerified: true,
      createdAt: DateTime.parse('2024-01-15T10:30:00.000Z'),
    );

    group('login', () {
      test('normalizes phone number and calls repository', () async {
        when(mockRepository.login('9647701234567', 'Password123'))
            .thenAnswer((_) async => testUser);

        final result = await authService.login('964 770 123 4567', 'Password123');

        expect(result, testUser);
        verify(mockRepository.login('9647701234567', 'Password123')).called(1);
      });

      test('handles phone with spaces and hyphens', () async {
        when(mockRepository.login('9647701234567', 'Password123'))
            .thenAnswer((_) async => testUser);

        await authService.login('964-770-123-4567', 'Password123');

        verify(mockRepository.login('9647701234567', 'Password123')).called(1);
      });

      test('handles phone with country code prefix', () async {
        when(mockRepository.login('+9647701234567', 'Password123'))
            .thenAnswer((_) async => testUser);

        await authService.login('+964 770 123 4567', 'Password123');

        verify(mockRepository.login('+9647701234567', 'Password123')).called(1);
      });
    });

    group('signup', () {
      test('normalizes phone number and calls repository', () async {
        when(mockRepository.signup('9647701234567', 'Password123'))
            .thenAnswer((_) async => testUser);

        final result = await authService.signup('964 770 123 4567', 'Password123');

        expect(result, testUser);
        verify(mockRepository.signup('9647701234567', 'Password123')).called(1);
      });

      test('handles phone with various formats', () async {
        when(mockRepository.signup('9647701234567', 'Password123'))
            .thenAnswer((_) async => testUser);

        await authService.signup('(964) 770-123-4567', 'Password123');

        verify(mockRepository.signup('9647701234567', 'Password123')).called(1);
      });
    });

    group('logout', () {
      test('calls repository logout', () async {
        when(mockRepository.logout()).thenAnswer((_) async => {});

        await authService.logout();

        verify(mockRepository.logout()).called(1);
      });
    });

    group('refreshToken', () {
      test('calls repository refreshToken', () async {
        when(mockRepository.refreshToken())
            .thenAnswer((_) async => testUser);

        final result = await authService.refreshToken();

        expect(result, testUser);
        verify(mockRepository.refreshToken()).called(1);
      });
    });

    group('getCurrentUser', () {
      test('calls repository getCurrentUser', () async {
        when(mockRepository.getCurrentUser())
            .thenAnswer((_) async => testUser);

        final result = await authService.getCurrentUser();

        expect(result, testUser);
        verify(mockRepository.getCurrentUser()).called(1);
      });
    });

    group('mapErrorMessage', () {
      test('maps INVALID_CREDENTIALS to user-friendly message', () {
        final exception = HttpException(
          statusCode: 401,
          message: 'Invalid credentials',
          code: 'INVALID_CREDENTIALS',
        );

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Invalid phone number or password');
      });

      test('maps ACCOUNT_DEACTIVATED to user-friendly message', () {
        final exception = HttpException(
          statusCode: 403,
          message: 'Account deactivated',
          code: 'ACCOUNT_DEACTIVATED',
        );

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Account has been deactivated');
      });

      test('maps RATE_LIMIT_EXCEEDED to original message', () {
        final exception = HttpException(
          statusCode: 429,
          message: 'Too many login attempts. Try again in 30 minutes.',
          code: 'RATE_LIMIT_EXCEEDED',
        );

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Too many login attempts. Try again in 30 minutes.');
      });

      test('maps NetworkException to no internet message', () {
        final exception = NetworkException();

        final message = authService.mapErrorMessage(exception);

        expect(message, 'No internet connection');
      });

      test('maps TimeoutException to timeout message', () {
        final exception = TimeoutException();

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Request timeout. Please try again.');
      });

      test('maps UnauthorizedException to session expired message', () {
        final exception = UnauthorizedException();

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Session expired. Please login again.');
      });

      test('maps unknown HttpException to original message', () {
        final exception = HttpException(
          statusCode: 500,
          message: 'Something went wrong',
          code: 'UNKNOWN_ERROR',
        );

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Something went wrong');
      });

      test('handles ServerException', () {
        final exception = ServerException(message: 'Database error');

        final message = authService.mapErrorMessage(exception);

        expect(message, 'Database error');
      });
    });
  });
}
