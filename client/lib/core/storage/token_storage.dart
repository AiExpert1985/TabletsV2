/// Token storage interface
abstract class TokenStorage {
  /// Save access token
  Future<void> saveAccessToken(String token);

  /// Get access token
  Future<String?> getAccessToken();

  /// Save refresh token
  Future<void> saveRefreshToken(String token);

  /// Get refresh token
  Future<String?> getRefreshToken();

  /// Clear all tokens (logout)
  Future<void> clearTokens();

  /// Check if user is authenticated (has tokens)
  Future<bool> hasTokens();
}
