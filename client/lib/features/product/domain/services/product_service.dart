import 'package:client/core/network/http_exception.dart';
import 'package:client/features/product/domain/entities/product.dart';
import 'package:client/features/product/domain/repositories/product_repository.dart';

/// Product service - handles business logic for product operations
class ProductService {
  final ProductRepository repository;

  ProductService(this.repository);

  /// Get all products with pagination
  Future<List<Product>> getProducts({int skip = 0, int limit = 100}) async {
    return await repository.getProducts(skip: skip, limit: limit);
  }

  /// Get product by ID
  Future<Product> getProductById(String id) async {
    return await repository.getProductById(id);
  }

  /// Map HTTP exception to user-friendly error message
  String mapErrorMessage(HttpException e) {
    if (e.code == 'PRODUCT_NOT_FOUND') {
      return 'Product not found';
    }
    if (e is NetworkException) {
      return 'No internet connection';
    }
    if (e is TimeoutException) {
      return 'Request timeout. Please try again.';
    }
    if (e is UnauthorizedException) {
      return 'You do not have permission to access products';
    }
    return e.message;
  }
}
