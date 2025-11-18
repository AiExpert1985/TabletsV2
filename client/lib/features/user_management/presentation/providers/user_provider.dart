import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/core/network/http_exception.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/user_management/data/datasources/user_remote_datasource.dart';
import 'package:client/features/user_management/data/models/user_create_dto.dart';
import 'package:client/features/user_management/data/models/user_update_dto.dart';
import 'package:client/features/user_management/data/repositories/user_repository_impl.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';

/// User repository provider
final userRepositoryProvider = Provider<UserRepository>((ref) {
  final httpClient = ref.watch(httpClientProvider);

  return UserRepositoryImpl(
    remoteDataSource: UserRemoteDataSource(httpClient),
  );
});

/// User management notifier - manages user CRUD operations
class UserNotifier extends StateNotifier<UserState> {
  final UserRepository userRepository;

  UserNotifier(this.userRepository) : super(UserInitial());

  /// Get all users (system admin only)
  Future<void> getUsers({int skip = 0, int limit = 100}) async {
    state = UserLoading();
    try {
      final users = await userRepository.getUsers(skip: skip, limit: limit);
      state = UsersLoaded(users);
    } on HttpException catch (e) {
      state = UserError(e.message);
    } catch (e) {
      state = UserError('Failed to load users: ${e.toString()}');
    }
  }

  /// Get user by ID (system admin only)
  Future<void> getUserById(String id) async {
    state = UserLoading();
    try {
      final user = await userRepository.getUserById(id);
      state = UserLoaded(user);
    } on HttpException catch (e) {
      state = UserError(e.message);
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
      final dto = UserCreateDto(
        phoneNumber: phoneNumber,
        password: password,
        email: email,
        companyId: companyId,
        role: role,
        isActive: isActive,
      );

      final user = await userRepository.createUser(dto);
      state = UserCreated(user);
    } on HttpException catch (e) {
      state = UserError(e.message);
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
      final dto = UserUpdateDto(
        phoneNumber: phoneNumber,
        email: email,
        password: password,
        companyId: companyId,
        role: role,
        isActive: isActive,
      );

      if (dto.isEmpty) {
        state = UserError('No fields to update');
        return;
      }

      final user = await userRepository.updateUser(id, dto);
      state = UserUpdated(user);
    } on HttpException catch (e) {
      state = UserError(e.message);
    } catch (e) {
      state = UserError('Failed to update user: ${e.toString()}');
    }
  }

  /// Delete user (system admin only)
  Future<void> deleteUser(String id) async {
    state = UserLoading();
    try {
      await userRepository.deleteUser(id);
      state = UserDeleted();
    } on HttpException catch (e) {
      state = UserError(e.message);
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
  final repository = ref.watch(userRepositoryProvider);
  return UserNotifier(repository);
});

/// Users list provider (FutureProvider for simple read-only access)
final usersListProvider = FutureProvider<List<User>>((ref) async {
  final repository = ref.watch(userRepositoryProvider);
  return await repository.getUsers();
});
