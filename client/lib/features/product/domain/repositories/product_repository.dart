import 'package:client/features/product/domain/entities/product.dart';

/// Product repository interface
abstract class ProductRepository {
  /// Get all products
  Future<List<Product>> getProducts({int skip = 0, int limit = 100});

  /// Get product by ID
  Future<Product> getProductById(String id);

  /// Search products by name
  Future<List<Product>> searchProducts(String searchTerm, {int skip = 0, int limit = 100});
}
