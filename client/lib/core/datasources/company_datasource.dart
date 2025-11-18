import 'package:client/core/api/api_client.dart';
import 'package:client/core/models/company.dart';

/// Datasource for fetching companies from the API
class CompanyDataSource {
  final ApiClient _apiClient;

  CompanyDataSource(this._apiClient);

  /// Fetch all companies
  Future<List<Company>> getCompanies() async {
    final response = await _apiClient.get('/companies');
    final List<dynamic> data = response['data'] as List<dynamic>;
    return data.map((json) => Company.fromJson(json as Map<String, dynamic>)).toList();
  }
}
