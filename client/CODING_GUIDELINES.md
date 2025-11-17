# Flutter Client Coding Guidelines

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [State Management (Riverpod)](#state-management-riverpod)
3. [Data Flow & Layers](#data-flow--layers)
4. [Models vs Entities](#models-vs-entities)
5. [Error Handling](#error-handling)
6. [Testing Strategy](#testing-strategy)
7. [Code Style & Conventions](#code-style--conventions)
8. [UI & Localization](#ui--localization)

---

## Project Architecture

### Directory Structure

```
lib/
├── core/                           # Core infrastructure
│   ├── config/                     # App configuration
│   ├── network/                    # HTTP client, interceptors
│   ├── storage/                    # Secure storage
│   └── utils/                      # Validators, helpers
│
├── features/                       # Feature modules (domain-driven)
│   ├── auth/                       # Authentication feature
│   │   ├── data/
│   │   │   ├── models/            # JSON models (API contracts)
│   │   │   └── repositories/      # Data access implementation
│   │   ├── domain/
│   │   │   ├── entities/          # Business entities
│   │   │   ├── repositories/      # Repository interfaces (abstract)
│   │   │   └── services/          # Business logic
│   │   └── presentation/
│   │       ├── providers/         # Riverpod state providers
│   │       ├── screens/           # Full-screen widgets
│   │       └── widgets/           # Reusable UI components
│   │
│   ├── product/                    # Product management
│   └── company/                    # Company management
│
└── main.dart                       # App entry point
```

### Layer Separation

**Flow:** `Screen → Provider → Service → Repository → API`

- **Presentation:** Widgets, screens, providers (state management)
- **Domain:** Services (business logic), entities, repository interfaces
- **Data:** Models (JSON), repository implementations, API clients

**Rule:** Never skip layers. Screens call providers, providers call services, services call repositories.

---

## State Management (Riverpod)

### State Pattern: Sealed Classes

**Always use sealed classes for state, never enums.**

```dart
// ✅ CORRECT - Sealed classes (type-safe, compiler-enforced)
sealed class AuthState {}

class AuthStateInitial extends AuthState {}

class AuthStateLoading extends AuthState {}

class AuthStateAuthenticated extends AuthState {
  final User user;
  AuthStateAuthenticated(this.user);
}

class AuthStateUnauthenticated extends AuthState {
  final String? message;
  AuthStateUnauthenticated([this.message]);
}

class AuthStateError extends AuthState {
  final String message;
  AuthStateError(this.message);
}

// ❌ WRONG - Enums (not type-safe, can't carry data)
enum AuthStatus { initial, loading, authenticated, unauthenticated, error }
```

**Why sealed classes?**
- Compiler enforces exhaustive pattern matching
- Each state can carry its own data
- Impossible states become impossible (e.g., can't be loading AND authenticated)

### Provider Pattern

```dart
// Service provider (singleton)
final authServiceProvider = Provider<AuthService>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthService(repository);
});

// State notifier provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});
```

### State Notifier

```dart
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(AuthStateInitial());

  Future<void> login(String phone, String password) async {
    state = AuthStateLoading();
    try {
      final user = await _authService.login(phone, password);
      state = AuthStateAuthenticated(user);
    } catch (e) {
      state = AuthStateError(_mapErrorMessage(e));
    }
  }

  String _mapErrorMessage(Object error) {
    // Map technical errors to user-friendly messages
    if (error is NetworkException) return 'No internet connection';
    if (error is UnauthorizedException) return 'Invalid credentials';
    return 'An error occurred. Please try again.';
  }
}
```

### Widget State Consumption

```dart
class LoginScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return switch (authState) {
      AuthStateInitial() => _buildLoginForm(context, ref),
      AuthStateLoading() => const Center(child: CircularProgressIndicator()),
      AuthStateAuthenticated(:final user) => _navigateToHome(user),
      AuthStateUnauthenticated(:final message) => _buildLoginForm(context, ref, error: message),
      AuthStateError(:final message) => _buildError(message),
    };
  }
}
```

---

## Data Flow & Layers

### 1. Repository Interface (Domain)

```dart
// lib/features/auth/domain/repositories/auth_repository.dart
abstract class AuthRepository {
  Future<User> login(String phoneNumber, String password);
  Future<User> getCurrentUser();
  Future<void> logout();
}
```

### 2. Repository Implementation (Data)

```dart
// lib/features/auth/data/repositories/auth_repository_impl.dart
class AuthRepositoryImpl implements AuthRepository {
  final Dio _dio;
  final SecureTokenStorage _tokenStorage;

  @override
  Future<User> login(String phoneNumber, String password) async {
    final response = await _dio.post('/api/auth/login', data: {
      'phone_number': phoneNumber,
      'password': password,
    });

    final authResponse = AuthResponseModel.fromJson(response.data);
    await _tokenStorage.saveAccessToken(authResponse.accessToken);
    await _tokenStorage.saveRefreshToken(authResponse.refreshToken);

    return authResponse.user;
  }
}
```

### 3. Service (Domain)

```dart
// lib/features/auth/domain/services/auth_service.dart
class AuthService {
  final AuthRepository _repository;

  AuthService(this._repository);

  Future<User> login(String phoneNumber, String password) async {
    // Business logic: normalize phone before API call
    final normalizedPhone = PhoneValidator.normalize(phoneNumber);
    return await _repository.login(normalizedPhone, password);
  }
}
```

### 4. Provider (Presentation)

```dart
// lib/features/auth/presentation/providers/auth_provider.dart
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});
```

---

## Models vs Entities

### Decision: Pragmatic Inheritance

**Pattern:** Models extend entities when API structure matches entity structure.

```dart
// ✅ CORRECT (for this project)
// lib/features/auth/domain/entities/user.dart
class User {
  final String id;
  final String phoneNumber;
  final String? email;
  final String? companyId;

  User({
    required this.id,
    required this.phoneNumber,
    this.email,
    this.companyId,
  });
}

// lib/features/auth/data/models/user_model.dart
class UserModel extends User {
  UserModel({
    required super.id,
    required super.phoneNumber,
    super.email,
    super.companyId,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'],
      phoneNumber: json['phone_number'],
      email: json['email'],
      companyId: json['company_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'phone_number': phoneNumber,
      'email': email,
      'company_id': companyId,
    };
  }
}
```

**Why inheritance instead of separation?**
- API contract matches domain entity perfectly
- Avoids 100+ lines of mapping boilerplate
- Pragmatic over theoretically pure
- Project is small enough to maintain this

**When to separate:** If API and domain diverge significantly (e.g., different field names, nested structures), create separate model and entity classes.

---

## Error Handling

### Exception Hierarchy

```dart
// lib/core/exceptions/app_exceptions.dart
abstract class AppException implements Exception {
  final String message;
  AppException(this.message);
}

class NetworkException extends AppException {
  NetworkException([String? message]) : super(message ?? 'Network error');
}

class UnauthorizedException extends AppException {
  UnauthorizedException([String? message]) : super(message ?? 'Unauthorized');
}

class ValidationException extends AppException {
  ValidationException(String message) : super(message);
}
```

### Error Mapping (User-Friendly Messages)

```dart
String mapErrorMessage(Object error) {
  return switch (error) {
    NetworkException() => 'No internet connection. Please check your network.',
    UnauthorizedException() => 'Invalid phone number or password.',
    ValidationException(:final message) => message,
    DioException(type: DioExceptionType.connectionTimeout) => 'Connection timeout. Please try again.',
    DioException(type: DioExceptionType.receiveTimeout) => 'Server is taking too long to respond.',
    _ => 'An unexpected error occurred. Please try again.',
  };
}
```

### Provider Error Handling

```dart
Future<void> login(String phone, String password) async {
  state = AuthStateLoading();
  try {
    final user = await _authService.login(phone, password);
    state = AuthStateAuthenticated(user);
  } on AppException catch (e) {
    state = AuthStateError(e.message);
  } catch (e, stackTrace) {
    // Log unexpected errors
    debugPrint('Unexpected error: $e\n$stackTrace');
    state = AuthStateError('An unexpected error occurred');
  }
}
```

---

## Testing Strategy

### 80/20 Rule - Test High-Value Units

**Focus on:**
- ✅ Validators (pure functions, critical for data integrity)
- ✅ Models (JSON serialization, roundtrip conversions)
- ✅ Services (business logic, error handling)
- ✅ Token storage (authentication persistence)

**Skip (use integration tests instead):**
- ❌ Widgets (complex, use widget tests)
- ❌ Providers (state management, better tested end-to-end)
- ❌ UI screens (use golden/integration tests)

### Test Structure

```
test/
├── core/
│   ├── utils/
│   │   └── validators_test.dart           # Phone, password validators
│   └── storage/
│       └── secure_token_storage_test.dart # Token persistence
└── features/
    └── auth/
        ├── data/
        │   └── models/
        │       ├── user_model_test.dart              # JSON serialization
        │       ├── token_response_model_test.dart
        │       └── auth_response_model_test.dart
        └── domain/
            └── services/
                └── auth_service_test.dart             # Business logic
```

### Example Test (Model)

```dart
// test/features/auth/data/models/user_model_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('UserModel', () {
    test('fromJson creates model from valid JSON', () {
      final json = {
        'id': '123',
        'phone_number': '9647701234567',
        'email': 'test@example.com',
        'company_id': 'company-1',
      };

      final user = UserModel.fromJson(json);

      expect(user.id, '123');
      expect(user.phoneNumber, '9647701234567');
      expect(user.email, 'test@example.com');
      expect(user.companyId, 'company-1');
    });

    test('toJson converts model to JSON', () {
      final user = UserModel(
        id: '123',
        phoneNumber: '9647701234567',
        email: 'test@example.com',
        companyId: 'company-1',
      );

      final json = user.toJson();

      expect(json['id'], '123');
      expect(json['phone_number'], '9647701234567');
      expect(json['email'], 'test@example.com');
      expect(json['company_id'], 'company-1');
    });

    test('roundtrip conversion preserves data', () {
      final originalJson = {
        'id': '123',
        'phone_number': '9647701234567',
        'email': 'test@example.com',
        'company_id': 'company-1',
      };

      final user = UserModel.fromJson(originalJson);
      final convertedJson = user.toJson();

      expect(convertedJson, equals(originalJson));
    });
  });
}
```

### Example Test (Service with Mocks)

```dart
// test/features/auth/domain/services/auth_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

@GenerateMocks([AuthRepository])
void main() {
  late AuthService authService;
  late MockAuthRepository mockRepository;

  setUp(() {
    mockRepository = MockAuthRepository();
    authService = AuthService(mockRepository);
  });

  group('AuthService', () {
    test('login normalizes phone number before calling repository', () async {
      final testUser = User(id: '1', phoneNumber: '9647701234567');
      when(mockRepository.login('9647701234567', 'pass'))
          .thenAnswer((_) async => testUser);

      await authService.login('964 770 123 4567', 'pass');

      verify(mockRepository.login('9647701234567', 'pass')).called(1);
    });
  });
}
```

---

## Code Style & Conventions

### Naming Conventions

- **Classes:** PascalCase (`AuthService`, `UserModel`)
- **Files:** snake_case (`auth_service.dart`, `user_model.dart`)
- **Variables/Functions:** camelCase (`phoneNumber`, `getUserById`)
- **Constants:** lowerCamelCase (`const defaultTimeout = 30`)
- **Private:** Underscore prefix (`_repository`, `_mapError`)

### Widget Organization

```dart
class MyScreen extends ConsumerWidget {
  // 1. Constructor & fields
  const MyScreen({super.key});

  // 2. Build method
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Watch providers at the top
    final state = ref.watch(myProvider);
    final theme = Theme.of(context);

    // Build UI
    return Scaffold(
      appBar: _buildAppBar(),
      body: _buildBody(state),
    );
  }

  // 3. Private helper methods
  AppBar _buildAppBar() { ... }
  Widget _buildBody(MyState state) { ... }
}
```

### Async Patterns

```dart
// ✅ CORRECT - Async/await
Future<User> getUser() async {
  final response = await _dio.get('/api/user');
  return UserModel.fromJson(response.data);
}

// ❌ WRONG - .then() chains (harder to read)
Future<User> getUser() {
  return _dio.get('/api/user').then((response) {
    return UserModel.fromJson(response.data);
  });
}
```

### Null Safety

```dart
// ✅ CORRECT - Null-aware operators
final email = user.email ?? 'No email';
final companyName = user.company?.name ?? 'No company';

// ❌ WRONG - Unnecessary null checks
final email = user.email != null ? user.email : 'No email';
```

---

## UI & Localization

### Multi-Language Ready (English/Arabic)

**Design for RTL from the start:**

```dart
// ✅ CORRECT - Use Directionality-aware widgets
Row(
  textDirection: Directionality.of(context),
  children: [...],
)

// Use EdgeInsets.symmetric instead of left/right
Padding(
  padding: EdgeInsets.symmetric(horizontal: 16),
  child: ...,
)

// ❌ WRONG - Hard-coded direction
Row(
  textDirection: TextDirection.ltr,
  children: [...],
)

Padding(
  padding: EdgeInsets.only(left: 16, right: 8),
  child: ...,
)
```

### Localization Structure (Future)

```
lib/
├── l10n/
│   ├── app_en.arb  # English strings
│   └── app_ar.arb  # Arabic strings
```

---

## Key Patterns & Anti-Patterns

### ✅ DO

- Use sealed classes for state
- Separate concerns (presentation/domain/data)
- Normalize and validate data in services
- Map technical errors to user-friendly messages
- Test validators, models, and services
- Use `const` constructors when possible
- Handle errors explicitly (no silent failures)

### ❌ DON'T

- Skip layers (e.g., screen calling repository directly)
- Use enums for complex state
- Mix business logic in widgets
- Expose technical error messages to users
- Test widgets in unit tests (use widget/integration tests)
- Use `dynamic` or ignore null safety
- Hard-code strings (use localization)

---

## Dependencies

### Core
- `flutter_riverpod` - State management
- `dio` - HTTP client
- `flutter_secure_storage` - Token persistence
- `go_router` - Navigation

### Testing
- `flutter_test` - Testing framework
- `mockito` - Mocking
- `build_runner` - Code generation (mocks)

---

## Quick Reference

### State Pattern Template

```dart
sealed class MyState {}
class MyStateInitial extends MyState {}
class MyStateLoading extends MyState {}
class MyStateSuccess extends MyState {
  final Data data;
  MyStateSuccess(this.data);
}
class MyStateError extends MyState {
  final String message;
  MyStateError(this.message);
}
```

### Provider Setup Template

```dart
// Repository
final myRepositoryProvider = Provider<MyRepository>((ref) {
  return MyRepositoryImpl(ref.watch(dioProvider));
});

// Service
final myServiceProvider = Provider<MyService>((ref) {
  return MyService(ref.watch(myRepositoryProvider));
});

// State Notifier
final myProvider = StateNotifierProvider<MyNotifier, MyState>((ref) {
  return MyNotifier(ref.watch(myServiceProvider));
});
```

---

**Last Updated:** 2025-11-17
**Flutter Version:** 3.x
**Riverpod Version:** 2.x
