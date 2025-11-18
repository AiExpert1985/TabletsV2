import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/features/auth/presentation/providers/auth_provider.dart';
import 'package:client/core/datasources/company_datasource.dart';
import 'package:client/core/models/company.dart';

/// Provider for company datasource
final companyDataSourceProvider = Provider<CompanyDataSource>((ref) {
  final httpClient = ref.watch(httpClientProvider);
  return CompanyDataSource(httpClient);
});

/// Provider for fetching companies list
final companiesProvider = FutureProvider<List<Company>>((ref) async {
  final dataSource = ref.watch(companyDataSourceProvider);
  return dataSource.getCompanies();
});
