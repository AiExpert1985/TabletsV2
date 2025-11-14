import 'http_interceptor.dart';

/// Logging interceptor - logs all HTTP requests/responses
class LoggingInterceptor implements HttpInterceptor {
  @override
  Future<Map<String, dynamic>?> onRequest(
    String path,
    String method,
    Map<String, dynamic>? headers,
  ) async {
    print('[HTTP] $method $path');
    if (headers != null) {
      print('[HTTP] Headers: $headers');
    }
    return headers;
  }

  @override
  Future<void> onResponse(String path, int statusCode, data) async {
    print('[HTTP] Response: $statusCode $path');
  }

  @override
  Future<void> onError(String path, error) async {
    print('[HTTP] Error: $path - $error');
  }
}
