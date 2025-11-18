import 'package:client/core/config/app_config.dart';
import 'package:client/core/network/http_client.dart';
import 'package:client/core/models/company.dart';

/// Datasource for fetching companies from the API
class CompanyDataSource {
  final HttpClient httpClient;

  CompanyDataSource(this.httpClient);

  /// Fetch all companies
  Future<List<Company>> getCompanies() async {
    final response = await httpClient.get(AppConfig.companiesEndpoint);
    final List<dynamic> data = response.data as List<dynamic>;
    return data.map((json) => Company.fromJson(json as Map<String, dynamic>)).toList();
  }
}
