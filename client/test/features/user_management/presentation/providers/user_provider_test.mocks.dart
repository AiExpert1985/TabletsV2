// Manual mocks for user_provider_test.dart
import 'package:mockito/mockito.dart';
import 'package:client/features/user_management/domain/repositories/user_repository.dart';

class MockUserRepository extends Mock implements UserRepository {}
