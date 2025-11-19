import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/home/presentation/screens/home_screen.dart';
import 'package:client/core/config/app_config.dart';

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
      final httpClient = ref.read(httpClientProvider);
      final response = await httpClient.get(AppConfig.usersEndpoint);
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

  Future<void> _showCreateUserDialog() async {
    final phoneController = TextEditingController();
    final passwordController = TextEditingController();
    final emailController = TextEditingController();
    String selectedRole = 'viewer';

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create User'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: phoneController,
                decoration: const InputDecoration(
                  labelText: 'Phone Number',
                  hintText: '07701234567',
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Password',
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: 'Email (optional)',
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: selectedRole,
                decoration: const InputDecoration(labelText: 'Role'),
                items: const [
                  DropdownMenuItem(value: 'viewer', child: Text('Viewer')),
                  DropdownMenuItem(value: 'salesperson', child: Text('Salesperson')),
                  DropdownMenuItem(value: 'accountant', child: Text('Accountant')),
                  DropdownMenuItem(value: 'company_admin', child: Text('Company Admin')),
                  DropdownMenuItem(value: 'system_admin', child: Text('System Admin')),
                ],
                onChanged: (value) {
                  if (value != null) selectedRole = value;
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (phoneController.text.isEmpty || passwordController.text.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Phone and password are required')),
                );
                return;
              }
              Navigator.pop(context, true);
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );

    if (result == true) {
      try {
        final httpClient = ref.read(httpClientProvider);
        await httpClient.post(AppConfig.usersEndpoint, data: {
          'phone_number': phoneController.text,
          'password': passwordController.text,
          if (emailController.text.isNotEmpty) 'email': emailController.text,
          'role': selectedRole,
          'is_active': true,
        });
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User created successfully')),
        );
        _loadUsers();
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  Future<void> _showEditUserDialog(Map<String, dynamic> user) async {
    final phoneController = TextEditingController(text: user['phone_number']);
    final emailController = TextEditingController(text: user['email'] ?? '');
    final passwordController = TextEditingController();
    String selectedRole = user['role'] ?? 'viewer';
    bool isActive = user['is_active'] ?? true;

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Edit User'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: phoneController,
                  decoration: const InputDecoration(labelText: 'Phone Number'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'New Password (leave blank to keep current)',
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: emailController,
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: selectedRole,
                  decoration: const InputDecoration(labelText: 'Role'),
                  items: const [
                    DropdownMenuItem(value: 'viewer', child: Text('Viewer')),
                    DropdownMenuItem(value: 'salesperson', child: Text('Salesperson')),
                    DropdownMenuItem(value: 'accountant', child: Text('Accountant')),
                    DropdownMenuItem(value: 'company_admin', child: Text('Company Admin')),
                    DropdownMenuItem(value: 'system_admin', child: Text('System Admin')),
                  ],
                  onChanged: (value) {
                    if (value != null) {
                      setState(() => selectedRole = value);
                    }
                  },
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  title: const Text('Active'),
                  value: isActive,
                  onChanged: (value) {
                    setState(() => isActive = value);
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );

    if (result == true) {
      try {
        final httpClient = ref.read(httpClientProvider);
        final updateData = <String, dynamic>{
          if (phoneController.text != user['phone_number'])
            'phone_number': phoneController.text,
          if (emailController.text != (user['email'] ?? ''))
            'email': emailController.text.isEmpty ? null : emailController.text,
          if (passwordController.text.isNotEmpty)
            'password': passwordController.text,
          if (selectedRole != user['role'])
            'role': selectedRole,
          if (isActive != user['is_active'])
            'is_active': isActive,
        };

        if (updateData.isNotEmpty) {
          await httpClient.put('${AppConfig.usersEndpoint}/${user['id']}',
              data: updateData);
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('User updated successfully')),
          );
          _loadUsers();
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
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
        final httpClient = ref.read(httpClientProvider);
        await httpClient.delete('${AppConfig.usersEndpoint}/$userId');
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User deleted successfully')),
        );
        _loadUsers();
      } catch (e) {
        if (!mounted) return;
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
                                          if (value == 'edit') {
                                            _showEditUserDialog(user);
                                          } else if (value == 'delete') {
                                            _deleteUser(user['id'], user['phone_number']);
                                          }
                                        },
                                        itemBuilder: (context) => [
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
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateUserDialog,
        tooltip: 'Create User',
        child: const Icon(Icons.add),
      ),
    );
  }
}
