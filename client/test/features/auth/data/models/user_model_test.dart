import 'package:flutter_test/flutter_test.dart';
import 'package:client/features/auth/data/models/user_model.dart';

void main() {
  group('UserModel', () {
    final testDateTime = DateTime.parse('2024-01-15T10:30:00.000Z');
    final testLoginDateTime = DateTime.parse('2024-01-15T11:00:00.000Z');

    final Map<String, dynamic> validJson = {
      'id': '123e4567-e89b-12d3-a456-426614174000',
      'phone_number': '9647701234567',
      'email': 'test@example.com',
      'company_id': '223e4567-e89b-12d3-a456-426614174000',
      'role': 'salesperson',
      'permissions': ['read:products', 'write:products'],
      'is_active': true,
      'is_phone_verified': true,
      'created_at': '2024-01-15T10:30:00.000Z',
      'last_login_at': '2024-01-15T11:00:00.000Z',
    };

    group('fromJson', () {
      test('creates UserModel from valid JSON with all fields', () {
        final user = UserModel.fromJson(validJson);

        expect(user.id, '123e4567-e89b-12d3-a456-426614174000');
        expect(user.phoneNumber, '9647701234567');
        expect(user.email, 'test@example.com');
        expect(user.companyId, '223e4567-e89b-12d3-a456-426614174000');
        expect(user.role, 'salesperson');
        expect(user.permissions, ['read:products', 'write:products']);
        expect(user.isActive, true);
        expect(user.isPhoneVerified, true);
        expect(user.createdAt, testDateTime);
        expect(user.lastLoginAt, testLoginDateTime);
      });

      test('creates UserModel with null optional fields', () {
        final json = {
          'id': '123e4567-e89b-12d3-a456-426614174000',
          'phone_number': '9647701234567',
          'email': null,
          'company_id': null,
          'role': 'system_admin',
          'permissions': null,
          'is_active': true,
          'is_phone_verified': true,
          'created_at': '2024-01-15T10:30:00.000Z',
          'last_login_at': null,
        };

        final user = UserModel.fromJson(json);

        expect(user.email, null);
        expect(user.companyId, null);
        expect(user.permissions, []);
        expect(user.lastLoginAt, null);
      });

      test('creates UserModel for system admin', () {
        final json = {
          'id': '123e4567-e89b-12d3-a456-426614174000',
          'phone_number': '9647701234567',
          'email': 'admin@example.com',
          'company_id': null,
          'role': 'system_admin',
          'permissions': ['*'],
          'is_active': true,
          'is_phone_verified': true,
          'created_at': '2024-01-15T10:30:00.000Z',
          'last_login_at': null,
        };

        final user = UserModel.fromJson(json);

        expect(user.role, 'system_admin');
        expect(user.companyId, null);
        expect(user.permissions, ['*']);
      });

      test('handles empty permissions array', () {
        final json = {
          'id': '123e4567-e89b-12d3-a456-426614174000',
          'phone_number': '9647701234567',
          'email': null,
          'company_id': '223e4567-e89b-12d3-a456-426614174000',
          'role': 'viewer',
          'permissions': [],
          'is_active': true,
          'is_phone_verified': false,
          'created_at': '2024-01-15T10:30:00.000Z',
          'last_login_at': null,
        };

        final user = UserModel.fromJson(json);

        expect(user.permissions, []);
      });

      test('parses ISO 8601 datetime strings correctly', () {
        final user = UserModel.fromJson(validJson);

        expect(user.createdAt.year, 2024);
        expect(user.createdAt.month, 1);
        expect(user.createdAt.day, 15);
        expect(user.createdAt.hour, 10);
        expect(user.createdAt.minute, 30);
      });
    });

    group('toJson', () {
      test('converts UserModel to JSON with all fields', () {
        final user = UserModel(
          id: '123e4567-e89b-12d3-a456-426614174000',
          phoneNumber: '9647701234567',
          email: 'test@example.com',
          companyId: '223e4567-e89b-12d3-a456-426614174000',
          role: 'salesperson',
          permissions: ['read:products', 'write:products'],
          isActive: true,
          isPhoneVerified: true,
          createdAt: testDateTime,
          lastLoginAt: testLoginDateTime,
        );

        final json = user.toJson();

        expect(json['id'], '123e4567-e89b-12d3-a456-426614174000');
        expect(json['phone_number'], '9647701234567');
        expect(json['email'], 'test@example.com');
        expect(json['company_id'], '223e4567-e89b-12d3-a456-426614174000');
        expect(json['role'], 'salesperson');
        expect(json['permissions'], ['read:products', 'write:products']);
        expect(json['is_active'], true);
        expect(json['is_phone_verified'], true);
        expect(json['created_at'], '2024-01-15T10:30:00.000Z');
        expect(json['last_login_at'], '2024-01-15T11:00:00.000Z');
      });

      test('converts UserModel to JSON with null optional fields', () {
        final user = UserModel(
          id: '123e4567-e89b-12d3-a456-426614174000',
          phoneNumber: '9647701234567',
          email: null,
          companyId: null,
          role: 'system_admin',
          permissions: ['*'],
          isActive: true,
          isPhoneVerified: true,
          createdAt: testDateTime,
          lastLoginAt: null,
        );

        final json = user.toJson();

        expect(json['email'], null);
        expect(json['company_id'], null);
        expect(json['last_login_at'], null);
      });

      test('converts datetime to ISO 8601 format', () {
        final user = UserModel(
          id: '123e4567-e89b-12d3-a456-426614174000',
          phoneNumber: '9647701234567',
          role: 'viewer',
          isActive: true,
          isPhoneVerified: true,
          createdAt: testDateTime,
        );

        final json = user.toJson();

        expect(json['created_at'], '2024-01-15T10:30:00.000Z');
      });
    });

    group('fromJson then toJson', () {
      test('roundtrip conversion preserves all data', () {
        final user = UserModel.fromJson(validJson);
        final json = user.toJson();

        expect(json['id'], validJson['id']);
        expect(json['phone_number'], validJson['phone_number']);
        expect(json['email'], validJson['email']);
        expect(json['company_id'], validJson['company_id']);
        expect(json['role'], validJson['role']);
        expect(json['permissions'], validJson['permissions']);
        expect(json['is_active'], validJson['is_active']);
        expect(json['is_phone_verified'], validJson['is_phone_verified']);
        expect(json['created_at'], validJson['created_at']);
        expect(json['last_login_at'], validJson['last_login_at']);
      });
    });

    group('toEntity', () {
      test('returns itself (UserModel extends User)', () {
        final user = UserModel(
          id: '123e4567-e89b-12d3-a456-426614174000',
          phoneNumber: '9647701234567',
          role: 'viewer',
          isActive: true,
          isPhoneVerified: true,
          createdAt: testDateTime,
        );

        final entity = user.toEntity();

        expect(entity, same(user));
      });
    });
  });
}
