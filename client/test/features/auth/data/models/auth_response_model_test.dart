import 'package:flutter_test/flutter_test.dart';
import 'package:client/features/auth/data/models/auth_response_model.dart';
import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/auth/data/models/token_response_model.dart';

void main() {
  group('AuthResponseModel', () {
    final Map<String, dynamic> validJson = {
      'user': {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'phone_number': '9647701234567',
        'email': 'test@example.com',
        'company_id': '223e4567-e89b-12d3-a456-426614174000',
        'role': 'user',
        'company_roles': ['sales'],
        'permissions': ['read:products'],
        'is_active': true,
        'is_phone_verified': true,
        'created_at': '2024-01-15T10:30:00.000Z',
        'last_login_at': '2024-01-15T11:00:00.000Z',
      },
      'tokens': {
        'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
        'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
        'token_type': 'bearer',
        'expires_in': 900,
      },
    };

    group('fromJson', () {
      test('creates AuthResponseModel from valid JSON', () {
        final authResponse = AuthResponseModel.fromJson(validJson);

        // User fields
        expect(authResponse.user.id, '123e4567-e89b-12d3-a456-426614174000');
        expect(authResponse.user.phoneNumber, '9647701234567');
        expect(authResponse.user.email, 'test@example.com');
        expect(authResponse.user.role, 'user');

        // Token fields
        expect(authResponse.tokens.accessToken, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access');
        expect(authResponse.tokens.refreshToken, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh');
        expect(authResponse.tokens.tokenType, 'bearer');
        expect(authResponse.tokens.expiresIn, 900);
      });

      test('creates AuthResponseModel for system admin', () {
        final json = {
          'user': {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'phone_number': '9647701234567',
            'email': 'admin@example.com',
            'company_id': null,
            'role': 'system_admin',
            'company_roles': [],
            'permissions': ['*'],
            'is_active': true,
            'is_phone_verified': true,
            'created_at': '2024-01-15T10:30:00.000Z',
            'last_login_at': null,
          },
          'tokens': {
            'access_token': 'access_token_here',
            'refresh_token': 'refresh_token_here',
            'token_type': 'bearer',
            'expires_in': 900,
          },
        };

        final authResponse = AuthResponseModel.fromJson(json);

        expect(authResponse.user.role, 'system_admin');
        expect(authResponse.user.companyId, null);
        expect(authResponse.user.permissions, ['*']);
      });

      test('user is of type UserModel', () {
        final authResponse = AuthResponseModel.fromJson(validJson);
        expect(authResponse.user, isA<UserModel>());
      });

      test('tokens is of type TokenResponseModel', () {
        final authResponse = AuthResponseModel.fromJson(validJson);
        expect(authResponse.tokens, isA<TokenResponseModel>());
      });
    });

    group('toJson', () {
      test('converts AuthResponseModel to JSON', () {
        final user = UserModel(
          id: '123e4567-e89b-12d3-a456-426614174000',
          name: 'Test User',
          phoneNumber: '9647701234567',
          email: 'test@example.com',
          companyId: '223e4567-e89b-12d3-a456-426614174000',
          role: 'user',
          permissions: ['read:products'],
          isActive: true,
          isPhoneVerified: true,
          createdAt: DateTime.parse('2024-01-15T10:30:00.000Z'),
          lastLoginAt: DateTime.parse('2024-01-15T11:00:00.000Z'),
        );

        final tokens = TokenResponseModel(
          accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
          refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
          tokenType: 'bearer',
          expiresIn: 900,
        );

        final authResponse = AuthResponseModel(user: user, tokens: tokens);
        final json = authResponse.toJson();

        // Check user object
        expect(json['user'], isA<Map<String, dynamic>>());
        expect(json['user']['id'], '123e4567-e89b-12d3-a456-426614174000');
        expect(json['user']['phone_number'], '9647701234567');

        // Check tokens object
        expect(json['tokens'], isA<Map<String, dynamic>>());
        expect(json['tokens']['access_token'], 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access');
      });
    });

    group('fromJson then toJson', () {
      test('roundtrip conversion preserves all data', () {
        final authResponse = AuthResponseModel.fromJson(validJson);
        final json = authResponse.toJson();

        // User data preserved
        expect(json['user']['id'], validJson['user']['id']);
        expect(json['user']['phone_number'], validJson['user']['phone_number']);
        expect(json['user']['role'], validJson['user']['role']);

        // Token data preserved
        expect(json['tokens']['access_token'], validJson['tokens']['access_token']);
        expect(json['tokens']['token_type'], validJson['tokens']['token_type']);
      });
    });

    group('nested object integrity', () {
      test('user object contains all required fields', () {
        final authResponse = AuthResponseModel.fromJson(validJson);
        final json = authResponse.toJson();

        expect(json['user']['id'], isNotNull);
        expect(json['user']['phone_number'], isNotNull);
        expect(json['user']['role'], isNotNull);
        expect(json['user']['is_active'], isNotNull);
        expect(json['user']['is_phone_verified'], isNotNull);
        expect(json['user']['created_at'], isNotNull);
      });

      test('tokens object contains all required fields', () {
        final authResponse = AuthResponseModel.fromJson(validJson);
        final json = authResponse.toJson();

        expect(json['tokens']['access_token'], isNotNull);
        expect(json['tokens']['refresh_token'], isNotNull);
        expect(json['tokens']['token_type'], isNotNull);
        expect(json['tokens']['expires_in'], isNotNull);
      });
    });
  });
}
