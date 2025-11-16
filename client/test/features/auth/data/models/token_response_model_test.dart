import 'package:flutter_test/flutter_test.dart';
import 'package:client/features/auth/data/models/token_response_model.dart';

void main() {
  group('TokenResponseModel', () {
    final Map<String, dynamic> validJson = {
      'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
      'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
      'token_type': 'bearer',
      'expires_in': 900,
    };

    group('fromJson', () {
      test('creates TokenResponseModel from valid JSON', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);

        expect(
          tokenResponse.accessToken,
          'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
        );
        expect(
          tokenResponse.refreshToken,
          'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
        );
        expect(tokenResponse.tokenType, 'bearer');
        expect(tokenResponse.expiresIn, 900);
      });

      test('handles different token types', () {
        final json = {
          'access_token': 'token123',
          'refresh_token': 'token456',
          'token_type': 'Bearer',
          'expires_in': 3600,
        };

        final tokenResponse = TokenResponseModel.fromJson(json);

        expect(tokenResponse.tokenType, 'Bearer');
        expect(tokenResponse.expiresIn, 3600);
      });

      test('handles different expiry times', () {
        final json = {
          'access_token': 'token123',
          'refresh_token': 'token456',
          'token_type': 'bearer',
          'expires_in': 604800, // 7 days
        };

        final tokenResponse = TokenResponseModel.fromJson(json);

        expect(tokenResponse.expiresIn, 604800);
      });
    });

    group('toJson', () {
      test('converts TokenResponseModel to JSON', () {
        final tokenResponse = TokenResponseModel(
          accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
          refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
          tokenType: 'bearer',
          expiresIn: 900,
        );

        final json = tokenResponse.toJson();

        expect(
          json['access_token'],
          'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
        );
        expect(
          json['refresh_token'],
          'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
        );
        expect(json['token_type'], 'bearer');
        expect(json['expires_in'], 900);
      });
    });

    group('fromJson then toJson', () {
      test('roundtrip conversion preserves all data', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);
        final json = tokenResponse.toJson();

        expect(json['access_token'], validJson['access_token']);
        expect(json['refresh_token'], validJson['refresh_token']);
        expect(json['token_type'], validJson['token_type']);
        expect(json['expires_in'], validJson['expires_in']);
      });
    });

    group('field types', () {
      test('access_token is String', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);
        expect(tokenResponse.accessToken, isA<String>());
      });

      test('refresh_token is String', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);
        expect(tokenResponse.refreshToken, isA<String>());
      });

      test('token_type is String', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);
        expect(tokenResponse.tokenType, isA<String>());
      });

      test('expires_in is int', () {
        final tokenResponse = TokenResponseModel.fromJson(validJson);
        expect(tokenResponse.expiresIn, isA<int>());
      });
    });
  });
}
