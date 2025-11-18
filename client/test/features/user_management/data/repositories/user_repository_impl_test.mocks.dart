// Manual mocks for user_repository_impl_test.dart
import 'package:mockito/mockito.dart';
import 'package:client/features/user_management/data/datasources/user_remote_datasource.dart';

class MockUserRemoteDataSource extends Mock implements UserRemoteDataSource {}
