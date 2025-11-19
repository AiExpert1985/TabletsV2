import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/user_management/data/datasources/user_remote_datasource.dart';
import 'package:client/features/user_management/data/repositories/user_repository_impl.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';
import 'package:client/features/user_management/domain/services/user_service.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';

/// User repository provider
final userRepositoryProvider = Provider<UserRepository>((ref) {
  final httpClient = ref.watch(httpClientProvider);

  return UserRepositoryImpl(
    remoteDataSource: UserRemoteDataSource(httpClient),
  );
});

/// User service provider
final userServiceProvider = Provider<UserService>((ref) {
  final repository = ref.watch(userRepositoryProvider);
  return UserService(repository);
});

/// User management notifier - manages user CRUD operations
class UserNotifier extends StateNotifier<UserState> {
  final UserService userService;

  UserNotifier(this.userService) : super(UserInitial());

  /// Get all users (system admin only)
  Future<void> getUsers({int skip = 0, int limit = 100}) async {
    state = UserLoading();
    try {
      final users = await userService.getUsers(skip: skip, limit: limit);
      state = UsersLoaded(users);
    } on HttpException catch (e) {
      state = UserError(userService.mapErrorMessage(e));
    } catch (e) {
      state = UserError('Failed to load users: ${e.toString()}');
    }
  }

  /// Get user by ID (system admin only)
  Future<void> getUserById(String id) async {
    state = UserLoading();
    try {
      final user = await userService.getUserById(id);
      state = UserLoaded(user);
    } on HttpException catch (e) {
      state = UserError(userService.mapErrorMessage(e));
    } catch (e) {
      state = UserError('Failed to load user: ${e.toString()}');
    }
  }

  /// Create a new user (system admin only)
  Future<void> createUser({
    required String phoneNumber,
    required String password,
    String? email,
    String? companyId,
    String role = 'viewer',
    bool isActive = true,
  }) async {
    state = UserLoading();
    try {
      final user = await userService.createUser(
        phoneNumber: phoneNumber,
        password: password,
        email: email,
        companyId: companyId,
        role: role,
        isActive: isActive,
      );
      state = UserCreated(user);
    } on HttpException catch (e) {
      state = UserError(userService.mapErrorMessage(e));
    } catch (e) {
      state = UserError('Failed to create user: ${e.toString()}');
    }
  }

  /// Update user (system admin only)
  Future<void> updateUser({
    required String id,
    String? phoneNumber,
    String? email,
    String? password,
    String? companyId,
    String? role,
    bool? isActive,
  }) async {
    state = UserLoading();
    try {
      final user = await userService.updateUser(
        id: id,
        phoneNumber: phoneNumber,
        email: email,
        password: password,
        companyId: companyId,
        role: role,
        isActive: isActive,
      );
      state = UserUpdated(user);
    } on HttpException catch (e) {
      state = UserError(userService.mapErrorMessage(e));
    } catch (e) {
      state = UserError('Failed to update user: ${e.toString()}');
    }
  }

  /// Delete user (system admin only)
  Future<void> deleteUser(String id) async {
    state = UserLoading();
    try {
      await userService.deleteUser(id);
      state = UserDeleted();
    } on HttpException catch (e) {
      state = UserError(userService.mapErrorMessage(e));
    } catch (e) {
      state = UserError('Failed to delete user: ${e.toString()}');
    }
  }

  /// Reset to initial state
  void reset() {
    state = UserInitial();
  }

  /// Clear error state
  void clearError() {
    if (state is UserError) {
      state = UserInitial();
    }
  }
}

/// User management provider
final userProvider = StateNotifierProvider<UserNotifier, UserState>((ref) {
  final service = ref.watch(userServiceProvider);
  return UserNotifier(service);
});

/// Users list provider (FutureProvider for simple read-only access)
final usersListProvider = FutureProvider<List<User>>((ref) async {
  final service = ref.watch(userServiceProvider);
  return await service.getUsers();
});
