/// Application configuration
class AppConfig {
  /// API base URL
  /// Use 127.0.0.1 for Windows desktop (more reliable than localhost)
  static const String baseUrl = 'http://127.0.0.1:8000';

  /// API endpoints
  static const String authEndpoint = '/api/auth';
  static const String usersEndpoint = '/api/users';
  static const String productsEndpoint = '/api/products';

  /// Timeout durations
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  /// Storage keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
