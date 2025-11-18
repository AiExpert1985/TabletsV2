import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:client/core/api/api_client.dart';
import 'package:client/core/datasources/company_datasource.dart';
import 'package:client/core/models/company.dart';

/// Provider for company datasource
final companyDataSourceProvider = Provider<CompanyDataSource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return CompanyDataSource(apiClient);
});

/// Provider for fetching companies list
final companiesProvider = FutureProvider<List<Company>>((ref) async {
  final dataSource = ref.watch(companyDataSourceProvider);
  return dataSource.getCompanies();
});
