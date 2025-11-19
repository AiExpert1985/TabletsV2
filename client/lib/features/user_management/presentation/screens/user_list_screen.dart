import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:client/core/authorization/permission_checker.dart';
import 'package:client/core/authorization/permissions.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/user_management/presentation/providers/user_provider.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';
import 'package:client/features/home/presentation/screens/home_screen.dart';

class UserListScreen extends ConsumerStatefulWidget {
  const UserListScreen({super.key});

  @override
  ConsumerState<UserListScreen> createState() => _UserListScreenState();
}

class _UserListScreenState extends ConsumerState<UserListScreen> {
  @override
  void initState() {
    super.initState();
    // Load users when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadUsers();
    });
  }

  void _loadUsers() {
    ref.read(userProvider.notifier).getUsers();
  }

  Future<void> _deleteUser(User user) async {
    final currentUser = _getCurrentUser();
    if (currentUser == null) return;

    // Check if trying to delete self
    if (user.id == currentUser.id) {
      _showError('You cannot delete yourself');
      return;
    }

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete User'),
        content: Text('Are you sure you want to delete ${user.phoneNumber}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      await ref.read(userProvider.notifier).deleteUser(user.id);

      final state = ref.read(userProvider);
      if (state is UserDeleted) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('User deleted successfully')),
          );
          _loadUsers();
        }
      } else if (state is UserError) {
        _showError(state.message);
      }
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  User? _getCurrentUser() {
    final authState = ref.read(authProvider);
    return authState is Authenticated ? authState.user : null;
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final currentUser = authState is Authenticated ? authState.user : null;

    // Authorization check - only admins can view users
    if (currentUser == null ||
        !PermissionChecker.hasPermission(currentUser, Permission.viewUsers)) {
      return Scaffold(
        appBar: AppBar(title: const Text('User Management')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.block, size: 64, color: Colors.red),
              SizedBox(height: 16),
              Text('Access Denied', style: TextStyle(fontSize: 20)),
              SizedBox(height: 8),
              Text('You do not have permission to view users'),
            ],
          ),
        ),
      );
    }

    final userState = ref.watch(userProvider);
    final canCreateUsers =
        PermissionChecker.hasPermission(currentUser, Permission.createUsers);

    return Scaffold(
      appBar: AppBar(
        title: const Text('User Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadUsers,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
      drawer: AppDrawer(user: currentUser),
      floatingActionButton: canCreateUsers
          ? FloatingActionButton.extended(
              onPressed: () {
                context.push('/user-management/create').then((_) => _loadUsers());
              },
              icon: const Icon(Icons.add),
              label: const Text('Add User'),
            )
          : null,
      body: _buildBody(userState, currentUser),
    );
  }

  Widget _buildBody(UserState userState, User currentUser) {
    return switch (userState) {
      UserLoading() => const Center(child: CircularProgressIndicator()),
      UsersLoaded(users: final users) => _buildUserList(users, currentUser),
      UserError(message: final message) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $message'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadUsers,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      _ => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('No users loaded'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadUsers,
                child: const Text('Load Users'),
              ),
            ],
          ),
        ),
    };
  }

  Widget _buildUserList(List<User> users, User currentUser) {
    if (users.isEmpty) {
      return const Center(
        child: Text('No users found'),
      );
    }

    final canEditUsers =
        PermissionChecker.hasPermission(currentUser, Permission.editUsers);
    final canDeleteUsers =
        PermissionChecker.hasPermission(currentUser, Permission.deleteUsers);

    return RefreshIndicator(
      onRefresh: () async => _loadUsers(),
      child: ListView.builder(
        itemCount: users.length,
        padding: const EdgeInsets.all(8),
        itemBuilder: (context, index) {
          final user = users[index];
          final isCurrentUser = user.id == currentUser.id;

          return Card(
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: user.isActive ? Colors.blue : Colors.grey,
                child: Icon(
                  user.role == UserRole.systemAdmin
                      ? Icons.admin_panel_settings
                      : Icons.person,
                  color: Colors.white,
                ),
              ),
              title: Text(user.phoneNumber),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Role: ${UserRole.displayName(user.role)}'),
                  if (user.email != null) Text('Email: ${user.email}'),
                  if (user.companyId != null)
                    Text('Company ID: ${user.companyId}'),
                  if (!user.isActive)
                    const Text(
                      'Inactive',
                      style: TextStyle(color: Colors.red),
                    ),
                ],
              ),
              trailing: isCurrentUser
                  ? const Chip(label: Text('You'))
                  : PopupMenuButton<String>(
                      onSelected: (value) {
                        if (value == 'edit' && canEditUsers) {
                          context
                              .push('/user-management/edit/${user.id}')
                              .then((_) => _loadUsers());
                        } else if (value == 'delete' && canDeleteUsers) {
                          _deleteUser(user);
                        }
                      },
                      itemBuilder: (context) => [
                        if (canEditUsers)
                          const PopupMenuItem(
                            value: 'edit',
                            child: Row(
                              children: [
                                Icon(Icons.edit, color: Colors.blue),
                                SizedBox(width: 8),
                                Text('Edit'),
                              ],
                            ),
                          ),
                        if (canDeleteUsers)
                          const PopupMenuItem(
                            value: 'delete',
                            child: Row(
                              children: [
                                Icon(Icons.delete, color: Colors.red),
                                SizedBox(width: 8),
                                Text('Delete'),
                              ],
                            ),
                          ),
                      ],
                    ),
              isThreeLine: true,
            ),
          );
        },
      ),
    );
  }
}
