import 'package:client/features/auth/domain/entities/user.dart';

/// Auth state
sealed class AuthState {}

/// Initial state (checking authentication)
class Initial extends AuthState {}

/// Loading state
class Loading extends AuthState {}

/// Authenticated state
class Authenticated extends AuthState {
  final User user;
  Authenticated(this.user);
}

/// Unauthenticated state
class Unauthenticated extends AuthState {}

/// Error state
class AuthError extends AuthState {
  final String message;
  AuthError(this.message);
}
