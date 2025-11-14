import 'package:client/features/auth/data/models/user_model.dart';
import 'package:client/features/auth/data/models/token_response_model.dart';

/// Auth response model (signup/login)
class AuthResponseModel {
  final UserModel user;
  final TokenResponseModel tokens;

  AuthResponseModel({
    required this.user,
    required this.tokens,
  });

  factory AuthResponseModel.fromJson(Map<String, dynamic> json) {
    return AuthResponseModel(
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
      tokens: TokenResponseModel.fromJson(json['tokens'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user': user.toJson(),
      'tokens': tokens.toJson(),
    };
  }
}
