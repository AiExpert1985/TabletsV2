/// HTTP interceptor interface
/// Allows modifying requests/responses (e.g., add auth token, log requests)
abstract class HttpInterceptor {
  /// Called before request is sent
  /// Return modified headers or null to use original
  Future<Map<String, dynamic>?> onRequest(
    String path,
    String method,
    Map<String, dynamic>? headers,
  );

  /// Called after response is received
  Future<void> onResponse(
    String path,
    int statusCode,
    dynamic data,
  );

  /// Called when error occurs
  Future<void> onError(
    String path,
    dynamic error,
  );
}
