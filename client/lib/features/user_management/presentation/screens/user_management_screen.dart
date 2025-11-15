import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/home/presentation/screens/home_screen.dart';
import 'package:dio/dio.dart';
import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/dio_client.dart';

class UserManagementScreen extends ConsumerStatefulWidget {
  const UserManagementScreen({super.key});

  @override
  ConsumerState<UserManagementScreen> createState() => _UserManagementScreenState();
}

class _UserManagementScreenState extends ConsumerState<UserManagementScreen> {
  List<Map<String, dynamic>> users = [];
  bool isLoading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState(() {
      isLoading = true;
      error = null;
    });

    try {
      final dio = ref.read(dioClientProvider);
      final response = await dio.get('${AppConfig.usersEndpoint}');
      setState(() {
        users = List<Map<String, dynamic>>.from(response.data);
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        error = e.toString();
        isLoading = false;
      });
    }
  }

  Future<void> _deleteUser(String userId, String phoneNumber) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete User'),
        content: Text('Are you sure you want to delete user $phoneNumber?'),
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

    if (confirm == true) {
      try {
        final dio = ref.read(dioClientProvider);
        await dio.delete('${AppConfig.usersEndpoint}/$userId');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User deleted successfully')),
        );
        _loadUsers();
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final currentUser = authState is Authenticated ? authState.user : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('User Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
      drawer: currentUser != null ? AppDrawer(user: currentUser) : null,
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Error: $error'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadUsers,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadUsers,
                  child: users.isEmpty
                      ? const Center(child: Text('No users found'))
                      : ListView.builder(
                          itemCount: users.length,
                          padding: const EdgeInsets.all(8),
                          itemBuilder: (context, index) {
                            final user = users[index];
                            final isCurrentUser = user['id'] == currentUser?.id;

                            return Card(
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: user['is_active'] ? Colors.blue : Colors.grey,
                                  child: Icon(
                                    user['role'] == 'system_admin'
                                        ? Icons.admin_panel_settings
                                        : Icons.person,
                                    color: Colors.white,
                                  ),
                                ),
                                title: Text(user['phone_number'] ?? 'Unknown'),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Role: ${user['role'] ?? 'unknown'}'),
                                    if (user['email'] != null)
                                      Text('Email: ${user['email']}'),
                                    if (!user['is_active'])
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
                                          if (value == 'delete') {
                                            _deleteUser(user['id'], user['phone_number']);
                                          }
                                        },
                                        itemBuilder: (context) => [
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
                ),
    );
  }
}
