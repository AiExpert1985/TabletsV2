import 'package:flutter_test/flutter_test.dart';
import 'package:client/core/authorization/role_permissions.dart';
import 'package:client/core/authorization/permissions.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';

void main() {
  group('RolePermissions', () {
    group('getPermissionsForRole', () {
      test('returns all permissions for system admin', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.systemAdmin);

        expect(permissions, equals(PermissionGroups.allPermissions));
        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.viewCompanies));
        expect(permissions, contains(Permission.createProducts));
      });

      test('returns correct permissions for company admin', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.companyAdmin);

        // Should have user management
        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.createUsers));
        expect(permissions, contains(Permission.editUsers));
        expect(permissions, contains(Permission.deleteUsers));

        // Should have product management
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, contains(Permission.createProducts));

        // Should NOT have company management
        expect(permissions, isNot(contains(Permission.viewCompanies)));
        expect(permissions, isNot(contains(Permission.createCompanies)));
      });

      test('returns correct permissions for accountant', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.accountant);

        // Should have read-only user access
        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, isNot(contains(Permission.createUsers)));

        // Should have financial permissions
        expect(permissions, contains(Permission.viewReports));
        expect(permissions, contains(Permission.viewFinancials));

        // Should have read-only product access
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, isNot(contains(Permission.createProducts)));
      });

      test('returns correct permissions for sales manager', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.salesManager);

        // Should have user read-only
        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, isNot(contains(Permission.createUsers)));

        // Should have full invoice management
        expect(permissions, contains(Permission.viewInvoices));
        expect(permissions, contains(Permission.createInvoices));
        expect(permissions, contains(Permission.editInvoices));
        expect(permissions, contains(Permission.deleteInvoices));

        // Should have product read-only
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, isNot(contains(Permission.createProducts)));
      });

      test('returns correct permissions for warehouse keeper', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.warehouseKeeper);

        // Should have full product management
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, contains(Permission.createProducts));
        expect(permissions, contains(Permission.editProducts));
        expect(permissions, contains(Permission.deleteProducts));

        // Should have warehouse management
        expect(permissions, contains(Permission.viewWarehouse));
        expect(permissions, contains(Permission.manageWarehouse));

        // Should NOT have user management
        expect(permissions, isNot(contains(Permission.viewUsers)));
        expect(permissions, isNot(contains(Permission.createUsers)));
      });

      test('returns correct permissions for salesperson', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.salesperson);

        // Should have product read-only
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, isNot(contains(Permission.createProducts)));

        // Should have limited invoice permissions
        expect(permissions, contains(Permission.viewInvoices));
        expect(permissions, contains(Permission.createInvoices));
        expect(permissions, isNot(contains(Permission.editInvoices)));
        expect(permissions, isNot(contains(Permission.deleteInvoices)));

        // Should NOT have user management
        expect(permissions, isNot(contains(Permission.createUsers)));
      });

      test('returns correct permissions for viewer', () {
        final permissions = RolePermissions.getPermissionsForRole(UserRole.viewer);

        // Should have read-only access to most features
        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, contains(Permission.viewInvoices));
        expect(permissions, contains(Permission.viewReports));

        // Should NOT have any create/edit/delete permissions
        expect(permissions, isNot(contains(Permission.createUsers)));
        expect(permissions, isNot(contains(Permission.editUsers)));
        expect(permissions, isNot(contains(Permission.createProducts)));
        expect(permissions, isNot(contains(Permission.createInvoices)));
      });

      test('returns empty set for unknown role', () {
        final permissions = RolePermissions.getPermissionsForRole('unknown_role');

        expect(permissions, isEmpty);
      });
    });

    group('Permission groups integrity', () {
      test('all permission groups are non-empty', () {
        expect(PermissionGroups.userManagement, isNotEmpty);
        expect(PermissionGroups.companyManagement, isNotEmpty);
        expect(PermissionGroups.productManagement, isNotEmpty);
        expect(PermissionGroups.invoiceManagement, isNotEmpty);
      });

      test('all permissions set contains all enum values', () {
        final allPermissions = PermissionGroups.allPermissions;
        final allEnumValues = Permission.values.toSet();

        expect(allPermissions, equals(allEnumValues));
      });

      test('read-only groups are subsets of full management groups', () {
        expect(
          PermissionGroups.userReadOnly.every(
            (p) => PermissionGroups.userManagement.contains(p),
          ),
          isTrue,
        );
        expect(
          PermissionGroups.productReadOnly.every(
            (p) => PermissionGroups.productManagement.contains(p),
          ),
          isTrue,
        );
      });
    });
  });
}
