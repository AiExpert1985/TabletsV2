import 'package:flutter_test/flutter_test.dart';
import 'package:client/core/utils/validators.dart';

void main() {
  group('PhoneValidator', () {
    group('normalize', () {
      test('removes spaces from phone number', () {
        expect(PhoneValidator.normalize('964 770 123 4567'), '9647701234567');
      });

      test('removes hyphens from phone number', () {
        expect(PhoneValidator.normalize('964-770-123-4567'), '9647701234567');
      });

      test('removes parentheses from phone number', () {
        expect(PhoneValidator.normalize('(964) 770-123-4567'), '9647701234567');
      });

      test('preserves plus sign', () {
        expect(PhoneValidator.normalize('+964 770 123 4567'), '+9647701234567');
      });

      test('returns original if empty after cleaning', () {
        expect(PhoneValidator.normalize('---'), '---');
      });

      test('handles already clean phone number', () {
        expect(PhoneValidator.normalize('9647701234567'), '9647701234567');
      });
    });

    group('isValid', () {
      test('returns true for non-empty phone', () {
        expect(PhoneValidator.isValid('9647701234567'), true);
      });

      test('returns false for empty phone', () {
        expect(PhoneValidator.isValid(''), false);
      });

      test('accepts any format (validation disabled)', () {
        expect(PhoneValidator.isValid('123'), true);
        expect(PhoneValidator.isValid('abc'), true);
      });
    });

    group('validate', () {
      test('returns null for valid phone', () {
        expect(PhoneValidator.validate('9647701234567'), null);
      });

      test('returns error for null phone', () {
        expect(
          PhoneValidator.validate(null),
          'Phone number is required',
        );
      });

      test('returns error for empty phone', () {
        expect(
          PhoneValidator.validate(''),
          'Phone number is required',
        );
      });

      test('returns null for any non-empty phone (validation disabled)', () {
        expect(PhoneValidator.validate('123'), null);
        expect(PhoneValidator.validate('abc'), null);
      });
    });
  });

  group('PasswordValidator', () {
    group('isStrong', () {
      test('returns true for strong password', () {
        expect(PasswordValidator.isStrong('StrongPass123'), true);
      });

      test('returns false for password without uppercase', () {
        expect(PasswordValidator.isStrong('weakpass123'), false);
      });

      test('returns false for password without lowercase', () {
        expect(PasswordValidator.isStrong('WEAKPASS123'), false);
      });

      test('returns false for password without digit', () {
        expect(PasswordValidator.isStrong('WeakPassword'), false);
      });

      test('returns false for short password', () {
        expect(PasswordValidator.isStrong('Pass1'), false);
      });

      test('returns false for too long password', () {
        final longPassword = 'A' * 100 + 'a' * 100 + '1';
        expect(PasswordValidator.isStrong(longPassword), false);
      });

      test('returns true for password with all requirements', () {
        expect(PasswordValidator.isStrong('MyPass123'), true);
      });
    });

    group('validate', () {
      test('returns null for valid strong password', () {
        expect(PasswordValidator.validate('StrongPass123'), null);
      });

      test('returns error for null password', () {
        expect(
          PasswordValidator.validate(null),
          'Password is required',
        );
      });

      test('returns error for empty password', () {
        expect(
          PasswordValidator.validate(''),
          'Password is required',
        );
      });

      test('returns error for too short password', () {
        expect(
          PasswordValidator.validate('Pass1'),
          'Password must be at least 8 characters',
        );
      });

      test('returns error for too long password', () {
        final longPassword = 'A' * 130;
        expect(
          PasswordValidator.validate(longPassword),
          'Password too long (max 128 characters)',
        );
      });

      test('returns error for password without uppercase', () {
        expect(
          PasswordValidator.validate('weakpass123'),
          'Password must contain at least one uppercase letter',
        );
      });

      test('returns error for password without lowercase', () {
        expect(
          PasswordValidator.validate('WEAKPASS123'),
          'Password must contain at least one lowercase letter',
        );
      });

      test('returns error for password without digit', () {
        expect(
          PasswordValidator.validate('WeakPassword'),
          'Password must contain at least one digit',
        );
      });
    });

    group('getStrength', () {
      test('returns 0 for weak password', () {
        expect(PasswordValidator.getStrength('weak'), 0);
        expect(PasswordValidator.getStrength('pass'), 0);
      });

      test('returns 1 for medium password', () {
        expect(PasswordValidator.getStrength('Password123'), 1);
        expect(PasswordValidator.getStrength('Pass1234'), 1);
      });

      test('returns 2 for strong password with special chars', () {
        expect(PasswordValidator.getStrength('Password123!'), 2);
        expect(PasswordValidator.getStrength('MyP@ss123'), 2);
      });

      test('handles empty password', () {
        expect(PasswordValidator.getStrength(''), 0);
      });
    });
  });

  group('ConfirmPasswordValidator', () {
    group('validate', () {
      test('returns null when passwords match', () {
        expect(
          ConfirmPasswordValidator.validate('Password123', 'Password123'),
          null,
        );
      });

      test('returns error when passwords do not match', () {
        expect(
          ConfirmPasswordValidator.validate('Password123', 'Password456'),
          'Passwords do not match',
        );
      });

      test('returns error for null confirm password', () {
        expect(
          ConfirmPasswordValidator.validate('Password123', null),
          'Please confirm your password',
        );
      });

      test('returns error for empty confirm password', () {
        expect(
          ConfirmPasswordValidator.validate('Password123', ''),
          'Please confirm your password',
        );
      });

      test('handles both null values', () {
        expect(
          ConfirmPasswordValidator.validate(null, null),
          'Please confirm your password',
        );
      });

      test('handles case-sensitive matching', () {
        expect(
          ConfirmPasswordValidator.validate('Password123', 'password123'),
          'Passwords do not match',
        );
      });
    });
  });
}
