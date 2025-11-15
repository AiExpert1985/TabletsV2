import 'package:client/features/product/domain/entities/product.dart';

/// Product model - JSON serialization
class ProductModel extends Product {
  ProductModel({
    required super.id,
    required super.companyId,
    required super.name,
    required super.sku,
    super.description,
    required super.costPrice,
    required super.sellingPrice,
    required super.stockQuantity,
    required super.reorderLevel,
    required super.isActive,
    required super.createdAt,
    required super.updatedAt,
  });

  /// From JSON
  factory ProductModel.fromJson(Map<String, dynamic> json) {
    return ProductModel(
      id: json['id'] as String,
      companyId: json['company_id'] as String,
      name: json['name'] as String,
      sku: json['sku'] as String,
      description: json['description'] as String?,
      costPrice: _parseDouble(json['cost_price']),
      sellingPrice: _parseDouble(json['selling_price']),
      stockQuantity: json['stock_quantity'] as int,
      reorderLevel: json['reorder_level'] as int,
      isActive: json['is_active'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Parse double from various formats (string, int, double)
  static double _parseDouble(dynamic value) {
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.parse(value);
    return 0.0;
  }

  /// To JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'company_id': companyId,
      'name': name,
      'sku': sku,
      'description': description,
      'cost_price': costPrice,
      'selling_price': sellingPrice,
      'stock_quantity': stockQuantity,
      'reorder_level': reorderLevel,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// Convert to entity
  Product toEntity() => this;
}
