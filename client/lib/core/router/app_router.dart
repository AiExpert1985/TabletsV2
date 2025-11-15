import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/screens/login_screen.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';
import 'package:client/features/home/presentation/screens/home_screen.dart';
import 'package:client/features/product/presentation/screens/product_list_screen.dart';
import 'package:client/features/user_management/presentation/screens/user_management_screen.dart';

/// App router configuration using go_router
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/auth/login',  // Fixed: was '/login'
    redirect: (context, state) {
      final isAuthenticated = authState is Authenticated;
      final isGoingToAuth = state.matchedLocation.startsWith('/auth');

      // If authenticated and trying to access auth screens, redirect to home
      if (isAuthenticated && isGoingToAuth) {
        return '/home';
      }

      // If not authenticated and not going to auth screens, redirect to login
      if (!isAuthenticated && !isGoingToAuth) {
        return '/auth/login';
      }

      return null; // No redirect
    },
    routes: [
      GoRoute(
        path: '/auth/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/products',
        name: 'products',
        builder: (context, state) => const ProductListScreen(),
      ),
      GoRoute(
        path: '/user-management',
        name: 'user-management',
        builder: (context, state) => const UserManagementScreen(),
      ),
    ],
  );
});
