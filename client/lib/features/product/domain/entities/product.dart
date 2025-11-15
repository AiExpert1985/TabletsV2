/// Product entity
class Product {
  final String id;
  final String companyId;
  final String name;
  final String sku;
  final String? description;
  final double costPrice;
  final double sellingPrice;
  final int stockQuantity;
  final int reorderLevel;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;

  Product({
    required this.id,
    required this.companyId,
    required this.name,
    required this.sku,
    this.description,
    required this.costPrice,
    required this.sellingPrice,
    required this.stockQuantity,
    required this.reorderLevel,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Check if product is low stock
  bool get isLowStock => stockQuantity <= reorderLevel;

  /// Calculate profit margin
  double get profitMargin {
    if (costPrice == 0) return 0;
    return ((sellingPrice - costPrice) / costPrice) * 100;
  }
}
