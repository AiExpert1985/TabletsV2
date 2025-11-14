import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/screens/login_screen.dart';
import 'package:client/features/auth/presentation/screens/signup_screen.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/auth/presentation/providers/auth_state.dart';

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
        path: '/auth/signup',
        name: 'signup',
        builder: (context, state) => const SignupScreen(),
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
    ],
  );
});

/// Placeholder home screen
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
      ),
      body: const Center(
        child: Text('Welcome! You are authenticated.'),
      ),
    );
  }
}
