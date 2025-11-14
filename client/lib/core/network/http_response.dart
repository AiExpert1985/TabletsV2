/// HTTP response wrapper
class HttpResponse<T> {
  final int statusCode;
  final T data;
  final Map<String, dynamic>? headers;

  HttpResponse({
    required this.statusCode,
    required this.data,
    this.headers,
  });

  bool get isSuccess => statusCode >= 200 && statusCode < 300;
}
