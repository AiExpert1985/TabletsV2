import 'package:client/features/auth/domain/entities/user.dart';

/// User management state
sealed class UserState {}

/// Initial state
class UserInitial extends UserState {}

/// Loading state
class UserLoading extends UserState {}

/// Users loaded successfully
class UsersLoaded extends UserState {
  final List<User> users;
  UsersLoaded(this.users);
}

/// User loaded successfully
class UserLoaded extends UserState {
  final User user;
  UserLoaded(this.user);
}

/// User created successfully
class UserCreated extends UserState {
  final User user;
  UserCreated(this.user);
}

/// User updated successfully
class UserUpdated extends UserState {
  final User user;
  UserUpdated(this.user);
}

/// User deleted successfully
class UserDeleted extends UserState {}

/// Error state
class UserError extends UserState {
  final String message;
  UserError(this.message);
}
