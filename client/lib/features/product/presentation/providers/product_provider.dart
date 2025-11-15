import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/features/product/data/datasources/product_remote_datasource.dart';
import 'package:client/features/product/data/repositories/product_repository_impl.dart';
import 'package:client/features/product/domain/entities/product.dart';
import 'package:client/features/product/domain/repositories/product_repository.dart';

/// Product repository provider
final productRepositoryProvider = Provider<ProductRepository>((ref) {
  final httpClient = ref.watch(httpClientProvider);

  return ProductRepositoryImpl(
    remoteDataSource: ProductRemoteDataSource(httpClient),
  );
});

/// Products list provider (async)
final productsProvider = FutureProvider<List<Product>>((ref) async {
  final repository = ref.watch(productRepositoryProvider);
  return await repository.getProducts();
});

/// Product by ID provider
final productByIdProvider = FutureProvider.family<Product, String>((ref, id) async {
  final repository = ref.watch(productRepositoryProvider);
  return await repository.getProductById(id);
});
