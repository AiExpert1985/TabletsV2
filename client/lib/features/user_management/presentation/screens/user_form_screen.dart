import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:client/core/authorization/permission_checker.dart';
import 'package:client/core/authorization/permissions.dart';
import 'package:client/core/providers/company_provider.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/user_management/presentation/providers/user_provider.dart';
import 'package:client/features/user_management/presentation/providers/user_state.dart';

class UserFormScreen extends ConsumerStatefulWidget {
  final String? userId; // null = create, non-null = edit

  const UserFormScreen({super.key, this.userId});

  @override
  ConsumerState<UserFormScreen> createState() => _UserFormScreenState();
}

class _UserFormScreenState extends ConsumerState<UserFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailController = TextEditingController();

  String _selectedRole = UserRole.viewer;
  String? _selectedCompanyId; // Selected company ID
  bool _isActive = true;
  bool _isLoading = false;
  User? _existingUser;

  bool get _isEditMode => widget.userId != null;

  @override
  void initState() {
    super.initState();
    if (_isEditMode) {
      // Delay provider update until after widget tree is built
      Future.microtask(() => _loadUser());
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  void _loadUser() {
    ref.read(userProvider.notifier).getUserById(widget.userId!);
  }

  void _populateForm(User user) {
    setState(() {
      _existingUser = user;
      _phoneController.text = user.phoneNumber;
      _emailController.text = user.email ?? '';
      _selectedCompanyId = user.companyId;
      _selectedRole = user.role;
      _isActive = user.isActive;
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    if (_isEditMode) {
      await ref.read(userProvider.notifier).updateUser(
            id: widget.userId!,
            phoneNumber: _phoneController.text.trim() != _existingUser?.phoneNumber
                ? _phoneController.text.trim()
                : null,
            email: _emailController.text.trim().isEmpty
                ? null
                : (_emailController.text.trim() != _existingUser?.email
                    ? _emailController.text.trim()
                    : null),
            password: _passwordController.text.trim().isEmpty
                ? null
                : _passwordController.text.trim(),
            companyId: _selectedCompanyId != _existingUser?.companyId
                ? _selectedCompanyId
                : null,
            role: _selectedRole != _existingUser?.role ? _selectedRole : null,
            isActive: _isActive != _existingUser?.isActive ? _isActive : null,
          );
    } else {
      await ref.read(userProvider.notifier).createUser(
            phoneNumber: _phoneController.text.trim(),
            password: _passwordController.text.trim(),
            email: _emailController.text.trim().isEmpty
                ? null
                : _emailController.text.trim(),
            companyId: _selectedCompanyId,
            role: _selectedRole,
            isActive: _isActive,
          );
    }

    setState(() => _isLoading = false);

    final state = ref.read(userProvider);
    if (state is UserCreated || state is UserUpdated) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              _isEditMode ? 'User updated successfully' : 'User created successfully',
            ),
          ),
        );
        context.pop();
      }
    } else if (state is UserError) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(state.message),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final currentUser = authState is Authenticated ? authState.user : null;

    // Authorization check
    final requiredPermission =
        _isEditMode ? Permission.editUsers : Permission.createUsers;

    if (currentUser == null ||
        !PermissionChecker.hasPermission(currentUser, requiredPermission)) {
      return Scaffold(
        appBar: AppBar(
          title: Text(_isEditMode ? 'Edit User' : 'Create User'),
        ),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.block, size: 64, color: Colors.red),
              SizedBox(height: 16),
              Text('Access Denied', style: TextStyle(fontSize: 20)),
              SizedBox(height: 8),
              Text('You do not have permission to perform this action'),
            ],
          ),
        ),
      );
    }

    // Watch user state to populate form in edit mode
    ref.listen<UserState>(userProvider, (previous, next) {
      if (next is UserLoaded && _isEditMode) {
        _populateForm(next.user);
      }
    });

    final userState = ref.watch(userProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditMode ? 'Edit User' : 'Create User'),
      ),
      body: _isEditMode && userState is UserLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextFormField(
                      controller: _phoneController,
                      decoration: const InputDecoration(
                        labelText: 'Phone Number',
                        hintText: '+964XXXXXXXXX',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.phone,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Phone number is required';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      decoration: InputDecoration(
                        labelText: _isEditMode
                            ? 'Password (leave empty to keep current)'
                            : 'Password',
                        border: const OutlineInputBorder(),
                      ),
                      obscureText: true,
                      validator: (value) {
                        if (!_isEditMode &&
                            (value == null || value.trim().isEmpty)) {
                          return 'Password is required';
                        }
                        if (value != null &&
                            value.trim().isNotEmpty &&
                            value.length < 8) {
                          return 'Password must be at least 8 characters';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(
                        labelText: 'Email (optional)',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.emailAddress,
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      value: _selectedRole,
                      decoration: const InputDecoration(
                        labelText: 'Role',
                        border: OutlineInputBorder(),
                      ),
                      items: UserRole.allRoles
                          .map((role) => DropdownMenuItem(
                                value: role,
                                child: Text(UserRole.displayName(role)),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() => _selectedRole = value);
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    // Company Dropdown
                    Consumer(
                      builder: (context, ref, child) {
                        final companiesAsync = ref.watch(companiesProvider);

                        return companiesAsync.when(
                          data: (companies) {
                            // Filter active companies only
                            final activeCompanies = companies.where((c) => c.isActive).toList();

                            return DropdownButtonFormField<String>(
                              value: _selectedCompanyId,
                              decoration: const InputDecoration(
                                labelText: 'Company',
                                hintText: 'Select a company',
                                border: OutlineInputBorder(),
                              ),
                              items: [
                                const DropdownMenuItem<String>(
                                  value: null,
                                  child: Text('None (System Admin only)'),
                                ),
                                ...activeCompanies.map((company) {
                                  return DropdownMenuItem<String>(
                                    value: company.id,
                                    child: Text(company.name),
                                  );
                                }),
                              ],
                              onChanged: (value) {
                                setState(() => _selectedCompanyId = value);
                              },
                              validator: (value) {
                                if (_selectedRole != UserRole.systemAdmin && value == null) {
                                  return 'Company is required for non-system-admin users';
                                }
                                return null;
                              },
                            );
                          },
                          loading: () => const LinearProgressIndicator(),
                          error: (error, stack) => Text('Error loading companies: $error'),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                    SwitchListTile(
                      title: const Text('Active'),
                      subtitle: const Text('User can log in and access the system'),
                      value: _isActive,
                      onChanged: (value) {
                        setState(() => _isActive = value);
                      },
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _isLoading ? null : _submit,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(_isEditMode ? 'Update User' : 'Create User'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
