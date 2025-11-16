# Flutter Unit Tests

Comprehensive unit tests for the TabletsV2 Flutter client following the 80/20 rule - focusing on the most critical 20% of code that provides 80% of the value.

## Test Coverage

### 1. Validators (`core/utils/validators_test.dart`)
**Why Critical:** Validates all user input, prevents security vulnerabilities

Tests:
- Phone number normalization and validation
- Password strength validation (min 8 chars, uppercase, lowercase, digit)
- Confirm password matching
- Edge cases (empty, null, too long, special chars)

### 2. Model Serialization (`features/auth/data/models/*_test.dart`)
**Why Critical:** Incorrect JSON parsing = app crashes or data corruption

Tests:
- `UserModel` - JSON serialization/deserialization
- `TokenResponseModel` - Authentication tokens
- `AuthResponseModel` - Login/signup responses
- Roundtrip conversions (fromJson → toJson → fromJson)
- Null handling for optional fields
- DateTime parsing (ISO 8601 format)

### 3. Auth Service (`features/auth/domain/services/auth_service_test.dart`)
**Why Critical:** Core business logic for authentication

Tests:
- Phone number normalization before API calls
- Login, signup, logout, refresh token, getCurrentUser
- Error message mapping (INVALID_CREDENTIALS, ACCOUNT_DEACTIVATED, etc.)
- Network exception handling
- Timeout handling

### 4. Token Storage (`core/storage/secure_token_storage_test.dart`)
**Why Critical:** Authentication persistence, security

Tests:
- Save/retrieve access token
- Save/retrieve refresh token
- Clear tokens (logout)
- hasTokens() logic (requires BOTH tokens)
- Integration scenarios (login flow, logout flow)
- Error handling

## Running Tests

### 1. Install Dependencies
```bash
cd client
flutter pub get
```

### 2. Generate Mock Files (Required First Time)
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates mock files for:
- `auth_service_test.mocks.dart` (MockAuthRepository)
- `secure_token_storage_test.mocks.dart` (MockFlutterSecureStorage)

### 3. Run All Tests
```bash
flutter test
```

### 4. Run Specific Test File
```bash
# Validators
flutter test test/core/utils/validators_test.dart

# User model
flutter test test/features/auth/data/models/user_model_test.dart

# Token storage
flutter test test/core/storage/secure_token_storage_test.dart

# Auth service
flutter test test/features/auth/domain/services/auth_service_test.dart
```

### 5. Run Tests with Coverage
```bash
flutter test --coverage
```

### 6. Run Specific Test Group
```bash
flutter test --name "PasswordValidator"
flutter test --name "hasTokens"
```

## Test Structure

```
test/
├── README.md
├── core/
│   ├── utils/
│   │   └── validators_test.dart          (Phone & password validation)
│   └── storage/
│       └── secure_token_storage_test.dart (Token persistence)
└── features/
    └── auth/
        ├── data/
        │   └── models/
        │       ├── user_model_test.dart          (User JSON)
        │       ├── token_response_model_test.dart (Token JSON)
        │       └── auth_response_model_test.dart  (Auth JSON)
        └── domain/
            └── services/
                └── auth_service_test.dart         (Business logic)
```

## Why These Tests? (80/20 Rule)

### High-Value Units Tested ✅
1. **Validators** - Prevent bad data from entering system
2. **Models** - Ensure API communication works
3. **Auth Service** - Core business logic
4. **Token Storage** - Authentication persistence

### Lower-Value Units NOT Tested (for now)
- UI widgets (use widget tests instead)
- Presentation providers (state management - more complex to test)
- HTTP interceptors (tested indirectly through integration tests)
- Routes/screens (use widget/integration tests)

## Common Issues

### Issue: Mock files not found
**Solution:** Run `flutter pub run build_runner build --delete-conflicting-outputs`

### Issue: Tests failing with "MissingStubError"
**Solution:** Make sure all mocked method calls have a corresponding `when()` stub in the test

### Issue: DateTime comparison failures
**Solution:** Use exact ISO 8601 strings from the test data

## Next Steps

After unit tests pass:
1. **Widget Tests** - Test UI components
2. **Integration Tests** - Test full user flows
3. **Golden Tests** - Test UI rendering
4. **Performance Tests** - Test app performance

## Test Metrics

Target Coverage:
- Validators: ~100% (critical for security)
- Models: ~95% (critical for API)
- Auth Service: ~90% (core business logic)
- Token Storage: ~90% (authentication)

Run `flutter test --coverage` to see actual coverage.
