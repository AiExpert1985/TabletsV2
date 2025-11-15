import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/http_client.dart';
import 'package:client/features/product/data/models/product_model.dart';

/// Product remote data source
class ProductRemoteDataSource {
  final HttpClient httpClient;

  ProductRemoteDataSource(this.httpClient);

  /// Get all products
  Future<List<ProductModel>> getProducts({int skip = 0, int limit = 100}) async {
    final response = await httpClient.get(
      AppConfig.productsEndpoint,
      queryParameters: {
        'skip': skip,
        'limit': limit,
      },
    );

    final List<dynamic> data = response.data as List<dynamic>;
    return data.map((json) => ProductModel.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Get product by ID
  Future<ProductModel> getProductById(String id) async {
    final response = await httpClient.get(
      '${AppConfig.productsEndpoint}/$id',
    );

    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Search products
  Future<List<ProductModel>> searchProducts(
    String searchTerm, {
    int skip = 0,
    int limit = 100,
  }) async {
    final response = await httpClient.get(
      '${AppConfig.productsEndpoint}/search',
      queryParameters: {
        'q': searchTerm,
        'skip': skip,
        'limit': limit,
      },
    );

    final List<dynamic> data = response.data as List<dynamic>;
    return data.map((json) => ProductModel.fromJson(json as Map<String, dynamic>)).toList();
  }
}
