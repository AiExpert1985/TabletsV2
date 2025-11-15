import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/auth/domain/entities/user.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState is Authenticated ? authState.user : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('TabletsV2 ERP'),
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
      drawer: user != null ? AppDrawer(user: user) : null,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.home,
              size: 80,
              color: Colors.blue,
            ),
            const SizedBox(height: 24),
            const Text(
              'Welcome to TabletsV2 ERP',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            if (user != null) ...[
              Text(
                'Phone: ${user.phoneNumber}',
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
              Text(
                'Role: ${user.role}',
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
              if (user.companyId != null)
                Text(
                  'Company ID: ${user.companyId}',
                  style: const TextStyle(fontSize: 14, color: Colors.grey),
                ),
            ],
            const SizedBox(height: 32),
            const Text(
              'Use the menu to navigate',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

class AppDrawer extends StatelessWidget {
  final User user;

  const AppDrawer({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.white,
                  child: Text(
                    user.phoneNumber.substring(0, 2).toUpperCase(),
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  user.phoneNumber,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  user.role.replaceAll('_', ' ').toUpperCase(),
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.home),
            title: const Text('Home'),
            onTap: () {
              Navigator.pop(context);
              context.go('/home');
            },
          ),
          ListTile(
            leading: const Icon(Icons.inventory),
            title: const Text('Products'),
            onTap: () {
              Navigator.pop(context);
              context.go('/products');
            },
          ),
          // Only show User Management for system admin
          if (user.isSystemAdmin) ...[
            const Divider(),
            ListTile(
              leading: const Icon(Icons.admin_panel_settings),
              title: const Text('User Management'),
              subtitle: const Text('System Admin Only'),
              onTap: () {
                Navigator.pop(context);
                context.go('/user-management');
              },
            ),
          ],
        ],
      ),
    );
  }
}
