/// Application configuration
class AppConfig {
  /// API base URL
  /// TODO: Update with your actual API URL
  static const String baseUrl = 'http://localhost:8000';

  /// API endpoints
  static const String authEndpoint = '/auth';

  /// Timeout durations
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  /// Storage keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
