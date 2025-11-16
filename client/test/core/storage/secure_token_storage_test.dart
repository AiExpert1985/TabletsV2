import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:client/core/storage/secure_token_storage.dart';
import 'package:client/core/config/app_config.dart';

import 'secure_token_storage_test.mocks.dart';

// Generate mocks
@GenerateMocks([FlutterSecureStorage])
void main() {
  late SecureTokenStorage storage;
  late MockFlutterSecureStorage mockSecureStorage;

  setUp(() {
    mockSecureStorage = MockFlutterSecureStorage();
    storage = SecureTokenStorage(storage: mockSecureStorage);
  });

  group('SecureTokenStorage', () {
    const testAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access';
    const testRefreshToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh';

    group('saveAccessToken', () {
      test('saves access token with correct key', () async {
        when(mockSecureStorage.write(
          key: AppConfig.accessTokenKey,
          value: testAccessToken,
        )).thenAnswer((_) async => {});

        await storage.saveAccessToken(testAccessToken);

        verify(mockSecureStorage.write(
          key: AppConfig.accessTokenKey,
          value: testAccessToken,
        )).called(1);
      });

      test('handles save errors gracefully', () async {
        when(mockSecureStorage.write(
          key: AppConfig.accessTokenKey,
          value: testAccessToken,
        )).thenThrow(Exception('Storage error'));

        expect(
          () => storage.saveAccessToken(testAccessToken),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('getAccessToken', () {
      test('returns access token when it exists', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);

        final result = await storage.getAccessToken();

        expect(result, testAccessToken);
        verify(mockSecureStorage.read(key: AppConfig.accessTokenKey)).called(1);
      });

      test('returns null when access token does not exist', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => null);

        final result = await storage.getAccessToken();

        expect(result, null);
      });

      test('uses correct storage key', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);

        await storage.getAccessToken();

        verify(mockSecureStorage.read(key: AppConfig.accessTokenKey)).called(1);
      });
    });

    group('saveRefreshToken', () {
      test('saves refresh token with correct key', () async {
        when(mockSecureStorage.write(
          key: AppConfig.refreshTokenKey,
          value: testRefreshToken,
        )).thenAnswer((_) async => {});

        await storage.saveRefreshToken(testRefreshToken);

        verify(mockSecureStorage.write(
          key: AppConfig.refreshTokenKey,
          value: testRefreshToken,
        )).called(1);
      });

      test('handles different refresh token formats', () async {
        const differentToken = 'different.refresh.token';
        when(mockSecureStorage.write(
          key: AppConfig.refreshTokenKey,
          value: differentToken,
        )).thenAnswer((_) async => {});

        await storage.saveRefreshToken(differentToken);

        verify(mockSecureStorage.write(
          key: AppConfig.refreshTokenKey,
          value: differentToken,
        )).called(1);
      });
    });

    group('getRefreshToken', () {
      test('returns refresh token when it exists', () async {
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        final result = await storage.getRefreshToken();

        expect(result, testRefreshToken);
        verify(mockSecureStorage.read(key: AppConfig.refreshTokenKey)).called(1);
      });

      test('returns null when refresh token does not exist', () async {
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => null);

        final result = await storage.getRefreshToken();

        expect(result, null);
      });
    });

    group('clearTokens', () {
      test('deletes both access and refresh tokens', () async {
        when(mockSecureStorage.delete(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => {});
        when(mockSecureStorage.delete(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => {});

        await storage.clearTokens();

        verify(mockSecureStorage.delete(key: AppConfig.accessTokenKey)).called(1);
        verify(mockSecureStorage.delete(key: AppConfig.refreshTokenKey)).called(1);
      });

      test('calls delete in correct order', () async {
        when(mockSecureStorage.delete(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => {});
        when(mockSecureStorage.delete(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => {});

        await storage.clearTokens();

        verifyInOrder([
          mockSecureStorage.delete(key: AppConfig.accessTokenKey),
          mockSecureStorage.delete(key: AppConfig.refreshTokenKey),
        ]);
      });

      test('handles delete errors', () async {
        when(mockSecureStorage.delete(key: AppConfig.accessTokenKey))
            .thenThrow(Exception('Delete error'));

        expect(
          () => storage.clearTokens(),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('hasTokens', () {
      test('returns true when both tokens exist', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        final result = await storage.hasTokens();

        expect(result, true);
      });

      test('returns false when access token is missing', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => null);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        final result = await storage.hasTokens();

        expect(result, false);
      });

      test('returns false when refresh token is missing', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => null);

        final result = await storage.hasTokens();

        expect(result, false);
      });

      test('returns false when both tokens are missing', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => null);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => null);

        final result = await storage.hasTokens();

        expect(result, false);
      });

      test('checks both tokens before returning', () async {
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        await storage.hasTokens();

        verify(mockSecureStorage.read(key: AppConfig.accessTokenKey)).called(1);
        verify(mockSecureStorage.read(key: AppConfig.refreshTokenKey)).called(1);
      });
    });

    group('integration scenarios', () {
      test('complete login flow - save and retrieve tokens', () async {
        // Save tokens
        when(mockSecureStorage.write(
          key: AppConfig.accessTokenKey,
          value: testAccessToken,
        )).thenAnswer((_) async => {});
        when(mockSecureStorage.write(
          key: AppConfig.refreshTokenKey,
          value: testRefreshToken,
        )).thenAnswer((_) async => {});

        await storage.saveAccessToken(testAccessToken);
        await storage.saveRefreshToken(testRefreshToken);

        // Retrieve tokens
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        final accessToken = await storage.getAccessToken();
        final refreshToken = await storage.getRefreshToken();
        final hasTokens = await storage.hasTokens();

        expect(accessToken, testAccessToken);
        expect(refreshToken, testRefreshToken);
        expect(hasTokens, true);
      });

      test('complete logout flow - clear tokens', () async {
        // Initially has tokens
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => testAccessToken);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => testRefreshToken);

        expect(await storage.hasTokens(), true);

        // Clear tokens
        when(mockSecureStorage.delete(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => {});
        when(mockSecureStorage.delete(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => {});

        await storage.clearTokens();

        // After clearing, no tokens
        when(mockSecureStorage.read(key: AppConfig.accessTokenKey))
            .thenAnswer((_) async => null);
        when(mockSecureStorage.read(key: AppConfig.refreshTokenKey))
            .thenAnswer((_) async => null);

        expect(await storage.hasTokens(), false);
      });
    });
  });
}
