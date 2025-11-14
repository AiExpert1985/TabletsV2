import 'dart:io';
import 'package:dio/dio.dart';
import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/http_client.dart';
import 'package:client/core/network/http_exception.dart' as app;
import 'package:client/core/network/http_response.dart';
import 'package:client/core/network/interceptors/http_interceptor.dart';

/// Dio implementation of HttpClient
/// This is the ONLY file that imports Dio directly
class DioHttpClient implements HttpClient {
  late final Dio _dio;
  final List<HttpInterceptor> _interceptors = [];

  DioHttpClient({String? baseUrl}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl ?? AppConfig.baseUrl,
        connectTimeout: AppConfig.connectTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
  }

  @override
  void addInterceptor(HttpInterceptor interceptor) {
    _interceptors.add(interceptor);
  }

  @override
  Future<HttpResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    return _request<T>(
      path,
      method: 'GET',
      queryParameters: queryParameters,
      headers: headers,
    );
  }

  @override
  Future<HttpResponse<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    return _request<T>(
      path,
      method: 'POST',
      data: data,
      queryParameters: queryParameters,
      headers: headers,
    );
  }

  @override
  Future<HttpResponse<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    return _request<T>(
      path,
      method: 'PUT',
      data: data,
      queryParameters: queryParameters,
      headers: headers,
    );
  }

  @override
  Future<HttpResponse<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    return _request<T>(
      path,
      method: 'DELETE',
      data: data,
      queryParameters: queryParameters,
      headers: headers,
    );
  }

  @override
  Future<HttpResponse<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    return _request<T>(
      path,
      method: 'PATCH',
      data: data,
      queryParameters: queryParameters,
      headers: headers,
    );
  }

  /// Internal request handler
  Future<HttpResponse<T>> _request<T>(
    String path, {
    required String method,
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
  }) async {
    try {
      // Apply interceptors (modify headers)
      Map<String, dynamic>? modifiedHeaders = headers;
      for (final interceptor in _interceptors) {
        modifiedHeaders = await interceptor.onRequest(path, method, modifiedHeaders);
      }

      // Make request
      final response = await _dio.request(
        path,
        data: data,
        queryParameters: queryParameters,
        options: Options(
          method: method,
          headers: modifiedHeaders,
        ),
      );

      // Notify interceptors of response
      for (final interceptor in _interceptors) {
        await interceptor.onResponse(path, response.statusCode ?? 0, response.data);
      }

      return HttpResponse<T>(
        statusCode: response.statusCode ?? 0,
        data: response.data as T,
        headers: response.headers.map,
      );
    } on DioException catch (e) {
      // Notify interceptors of error
      for (final interceptor in _interceptors) {
        await interceptor.onError(path, e);
      }

      throw _handleDioError(e);
    } catch (e) {
      // Notify interceptors of error
      for (final interceptor in _interceptors) {
        await interceptor.onError(path, e);
      }

      throw app.HttpException(message: e.toString());
    }
  }

  /// Convert DioException to app exceptions
  app.HttpException _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return app.TimeoutException();

      case DioExceptionType.connectionError:
        return app.NetworkException();

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final data = error.response?.data;

        // Try to extract error message from response
        String? message;
        String? code;

        if (data is Map<String, dynamic>) {
          if (data.containsKey('error')) {
            final errorObj = data['error'];
            if (errorObj is Map<String, dynamic>) {
              message = errorObj['message'] as String?;
              code = errorObj['code'] as String?;
            }
          } else if (data.containsKey('detail')) {
            final detail = data['detail'];
            if (detail is Map<String, dynamic>) {
              message = detail['message'] as String?;
              code = detail['code'] as String?;
            } else if (detail is String) {
              message = detail;
            }
          }
        }

        if (statusCode == 401) {
          return app.UnauthorizedException();
        } else if (statusCode != null && statusCode >= 500) {
          return app.ServerException(message: message);
        }

        return app.HttpException(
          statusCode: statusCode,
          message: message ?? 'Request failed',
          code: code,
        );

      case DioExceptionType.cancel:
        return app.HttpException(message: 'Request cancelled');

      case DioExceptionType.unknown:
        if (error.error is SocketException) {
          return app.NetworkException();
        }
        return app.HttpException(message: error.message ?? 'Unknown error');

      default:
        return app.HttpException(message: error.message ?? 'Unknown error');
    }
  }
}
