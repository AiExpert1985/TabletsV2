import 'package:client/core/storage/token_storage.dart';
import 'http_interceptor.dart';

/// Auth interceptor - adds Bearer token to requests
class AuthInterceptor implements HttpInterceptor {
  final TokenStorage tokenStorage;

  AuthInterceptor(this.tokenStorage);

  /// Public endpoints that don't require authentication
  final List<String> _publicEndpoints = [
    '/auth/signup',
    '/auth/login',
    '/auth/refresh',
    '/auth/password/request-reset',
    '/auth/password/reset',
  ];

  @override
  Future<Map<String, dynamic>?> onRequest(
    String path,
    String method,
    Map<String, dynamic>? headers,
  ) async {
    // Skip auth for public endpoints
    if (_publicEndpoints.any((endpoint) => path.contains(endpoint))) {
      return headers;
    }

    // Get access token for protected endpoints
    final token = await tokenStorage.getAccessToken();

    if (token != null) {
      // Add Authorization header
      final modifiedHeaders = Map<String, dynamic>.from(headers ?? {});
      modifiedHeaders['Authorization'] = 'Bearer $token';
      return modifiedHeaders;
    }

    return headers;
  }

  @override
  Future<void> onResponse(String path, int statusCode, data) async {
    // Can add response logging here if needed
  }

  @override
  Future<void> onError(String path, error) async {
    // Can add error logging here if needed
  }
}
