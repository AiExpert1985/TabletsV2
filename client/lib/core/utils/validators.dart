/// Phone number validator
class PhoneValidator {
  /// Normalize phone number to E.164 format
  static String normalize(String phone) {
    // Remove all non-digit characters except +
    String cleaned = phone.replaceAll(RegExp(r'[^\d+]'), '');

    // Remove leading + if present
    cleaned = cleaned.replaceFirst('+', '');

    // Handle different formats
    String number;
    if (cleaned.startsWith('964')) {
      // Already has country code
      number = cleaned;
    } else if (cleaned.startsWith('0')) {
      // Local format: 07501234567 -> 9647501234567
      number = '964${cleaned.substring(1)}';
    } else {
      // Assume missing leading 0: 7501234567 -> 9647501234567
      number = '964$cleaned';
    }

    return '+$number';
  }

  /// Validate Iraqi phone number format
  static bool isValid(String phone) {
    try {
      final normalized = normalize(phone);
      // Check format: +964 7XX XXX XXXX (always starts with 7, then operator 3-9)
      return RegExp(r'^\+9647[3-9]\d{7}$').hasMatch(normalized);
    } catch (e) {
      return false;
    }
  }

  /// Get validation error message
  static String? validate(String? phone) {
    if (phone == null || phone.isEmpty) {
      return 'Phone number is required';
    }

    if (!isValid(phone)) {
      return 'Invalid Iraqi phone number';
    }

    return null;
  }
}

/// Password validator
class PasswordValidator {
  /// Password requirements
  static const int minLength = 8;
  static const int maxLength = 128;

  /// Validate password strength
  static bool isStrong(String password) {
    if (password.length < minLength) return false;
    if (password.length > maxLength) return false;
    if (!RegExp(r'[A-Z]').hasMatch(password)) return false;
    if (!RegExp(r'[a-z]').hasMatch(password)) return false;
    if (!RegExp(r'\d').hasMatch(password)) return false;
    return true;
  }

  /// Get validation error message
  static String? validate(String? password) {
    if (password == null || password.isEmpty) {
      return 'Password is required';
    }

    if (password.length < minLength) {
      return 'Password must be at least $minLength characters';
    }

    if (password.length > maxLength) {
      return 'Password too long (max $maxLength characters)';
    }

    if (!RegExp(r'[A-Z]').hasMatch(password)) {
      return 'Password must contain at least one uppercase letter';
    }

    if (!RegExp(r'[a-z]').hasMatch(password)) {
      return 'Password must contain at least one lowercase letter';
    }

    if (!RegExp(r'\d').hasMatch(password)) {
      return 'Password must contain at least one digit';
    }

    return null;
  }

  /// Get password strength (0-3: weak, medium, strong)
  static int getStrength(String password) {
    int strength = 0;

    if (password.length >= minLength) strength++;
    if (RegExp(r'[A-Z]').hasMatch(password)) strength++;
    if (RegExp(r'[a-z]').hasMatch(password)) strength++;
    if (RegExp(r'\d').hasMatch(password)) strength++;
    if (RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(password)) strength++;

    // Normalize to 0-3
    if (strength <= 2) return 0; // weak
    if (strength == 3 || strength == 4) return 1; // medium
    return 2; // strong
  }
}

/// Confirm password validator
class ConfirmPasswordValidator {
  static String? validate(String? password, String? confirmPassword) {
    if (confirmPassword == null || confirmPassword.isEmpty) {
      return 'Please confirm your password';
    }

    if (password != confirmPassword) {
      return 'Passwords do not match';
    }

    return null;
  }
}
