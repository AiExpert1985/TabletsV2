import 'package:client/core/network/http_exception.dart';
import 'package:client/features/product/data/datasources/product_remote_datasource.dart';
import 'package:client/features/product/domain/entities/product.dart';
import 'package:client/features/product/domain/repositories/product_repository.dart';

/// Product repository implementation
class ProductRepositoryImpl implements ProductRepository {
  final ProductRemoteDataSource remoteDataSource;

  ProductRepositoryImpl({required this.remoteDataSource});

  @override
  Future<List<Product>> getProducts({int skip = 0, int limit = 100}) async {
    try {
      final products = await remoteDataSource.getProducts(skip: skip, limit: limit);
      return products.map((p) => p.toEntity()).toList();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<Product> getProductById(String id) async {
    try {
      final product = await remoteDataSource.getProductById(id);
      return product.toEntity();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }

  @override
  Future<List<Product>> searchProducts(
    String searchTerm, {
    int skip = 0,
    int limit = 100,
  }) async {
    try {
      final products = await remoteDataSource.searchProducts(
        searchTerm,
        skip: skip,
        limit: limit,
      );
      return products.map((p) => p.toEntity()).toList();
    } on HttpException {
      rethrow;
    } catch (e) {
      throw HttpException(message: e.toString());
    }
  }
}
