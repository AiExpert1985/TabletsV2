/// Custom HTTP exceptions
class HttpException implements Exception {
  final int? statusCode;
  final String message;
  final String? code;

  HttpException({
    this.statusCode,
    required this.message,
    this.code,
  });

  @override
  String toString() => 'HttpException: $message (Status: $statusCode, Code: $code)';
}

/// Network exceptions
class NetworkException extends HttpException {
  NetworkException() : super(message: 'No internet connection');
}

class TimeoutException extends HttpException {
  TimeoutException() : super(message: 'Request timeout');
}

class UnauthorizedException extends HttpException {
  UnauthorizedException()
      : super(
          statusCode: 401,
          message: 'Unauthorized',
          code: 'UNAUTHORIZED',
        );
}

class ServerException extends HttpException {
  ServerException({String? message})
      : super(
          statusCode: 500,
          message: message ?? 'Internal server error',
          code: 'SERVER_ERROR',
        );
}
