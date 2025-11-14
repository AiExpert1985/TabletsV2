import 'package:client/core/storage/token_storage.dart';
import 'http_interceptor.dart';

/// Auth interceptor - adds Bearer token to requests
class AuthInterceptor implements HttpInterceptor {
  final TokenStorage tokenStorage;

  AuthInterceptor(this.tokenStorage);

  @override
  Future<Map<String, dynamic>?> onRequest(
    String path,
    String method,
    Map<String, dynamic>? headers,
  ) async {
    // Get access token
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
