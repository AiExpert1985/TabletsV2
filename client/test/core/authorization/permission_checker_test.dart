import 'package:flutter_test/flutter_test.dart';
import 'package:client/core/authorization/permission_checker.dart';
import 'package:client/core/authorization/permissions.dart';
import 'package:client/features/auth/domain/entities/user.dart';
import 'package:client/features/auth/domain/entities/user_role.dart';

void main() {
  group('PermissionChecker', () {
    // Test users with different roles
    final systemAdminUser = User(
      id: '1',
      phoneNumber: '+9647701234567',
      role: UserRole.systemAdmin,
      isActive: true,
      isPhoneVerified: true,
      createdAt: DateTime.now(),
    );

    final companyAdminUser = User(
      id: '2',
      phoneNumber: '+9647701234568',
      companyId: 'company-1',
      role: UserRole.companyAdmin,
      isActive: true,
      isPhoneVerified: true,
      createdAt: DateTime.now(),
    );

    final accountantUser = User(
      id: '3',
      phoneNumber: '+9647701234569',
      companyId: 'company-1',
      role: UserRole.accountant,
      isActive: true,
      isPhoneVerified: true,
      createdAt: DateTime.now(),
    );

    final viewerUser = User(
      id: '4',
      phoneNumber: '+9647701234570',
      companyId: 'company-1',
      role: UserRole.viewer,
      isActive: true,
      isPhoneVerified: true,
      createdAt: DateTime.now(),
    );

    group('getUserPermissions', () {
      test('returns all permissions for system admin', () {
        final permissions = PermissionChecker.getUserPermissions(systemAdminUser);

        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.createUsers));
        expect(permissions, contains(Permission.viewCompanies));
        expect(permissions, contains(Permission.createProducts));
        expect(permissions.length, equals(28)); // Exact count of all permissions
      });

      test('returns correct permissions for company admin', () {
        final permissions = PermissionChecker.getUserPermissions(companyAdminUser);

        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.createUsers));
        expect(permissions, contains(Permission.editUsers));
        expect(permissions, contains(Permission.deleteUsers));
        expect(permissions, isNot(contains(Permission.viewCompanies))); // No company management
      });

      test('returns read-only permissions for viewer', () {
        final permissions = PermissionChecker.getUserPermissions(viewerUser);

        expect(permissions, contains(Permission.viewUsers));
        expect(permissions, contains(Permission.viewProducts));
        expect(permissions, isNot(contains(Permission.createUsers)));
        expect(permissions, isNot(contains(Permission.editUsers)));
        expect(permissions, isNot(contains(Permission.deleteUsers)));
      });

      test('returns empty set for unknown role', () {
        final unknownUser = User(
          id: '5',
          phoneNumber: '+9647701234571',
          role: 'unknown_role',
          isActive: true,
          isPhoneVerified: true,
          createdAt: DateTime.now(),
        );

        final permissions = PermissionChecker.getUserPermissions(unknownUser);

        expect(permissions, isEmpty);
      });
    });

    group('hasPermission', () {
      test('returns true when user has the permission', () {
        expect(
          PermissionChecker.hasPermission(systemAdminUser, Permission.createUsers),
          isTrue,
        );
        expect(
          PermissionChecker.hasPermission(companyAdminUser, Permission.viewUsers),
          isTrue,
        );
        expect(
          PermissionChecker.hasPermission(viewerUser, Permission.viewProducts),
          isTrue,
        );
      });

      test('returns false when user lacks the permission', () {
        expect(
          PermissionChecker.hasPermission(viewerUser, Permission.createUsers),
          isFalse,
        );
        expect(
          PermissionChecker.hasPermission(accountantUser, Permission.deleteUsers),
          isFalse,
        );
        expect(
          PermissionChecker.hasPermission(companyAdminUser, Permission.viewCompanies),
          isFalse,
        );
      });
    });

    group('hasAnyPermission', () {
      test('returns true when user has at least one permission', () {
        expect(
          PermissionChecker.hasAnyPermission(
            viewerUser,
            [Permission.createUsers, Permission.viewUsers],
          ),
          isTrue,
        );
      });

      test('returns false when user has none of the permissions', () {
        expect(
          PermissionChecker.hasAnyPermission(
            viewerUser,
            [Permission.createUsers, Permission.editUsers, Permission.deleteUsers],
          ),
          isFalse,
        );
      });

      test('returns true for system admin with any permission list', () {
        expect(
          PermissionChecker.hasAnyPermission(
            systemAdminUser,
            [Permission.createUsers, Permission.viewCompanies],
          ),
          isTrue,
        );
      });
    });

    group('hasAllPermissions', () {
      test('returns true when user has all permissions', () {
        expect(
          PermissionChecker.hasAllPermissions(
            companyAdminUser,
            [Permission.viewUsers, Permission.createUsers, Permission.editUsers],
          ),
          isTrue,
        );
      });

      test('returns false when user lacks any permission', () {
        expect(
          PermissionChecker.hasAllPermissions(
            viewerUser,
            [Permission.viewUsers, Permission.createUsers],
          ),
          isFalse,
        );
      });

      test('returns true for system admin with all permissions', () {
        expect(
          PermissionChecker.hasAllPermissions(
            systemAdminUser,
            [Permission.viewUsers, Permission.createUsers, Permission.viewCompanies],
          ),
          isTrue,
        );
      });
    });

    group('isSystemAdmin', () {
      test('returns true for system admin', () {
        expect(PermissionChecker.isSystemAdmin(systemAdminUser), isTrue);
      });

      test('returns false for non-system admin', () {
        expect(PermissionChecker.isSystemAdmin(companyAdminUser), isFalse);
        expect(PermissionChecker.isSystemAdmin(viewerUser), isFalse);
      });
    });

    group('isAdmin', () {
      test('returns true for system admin', () {
        expect(PermissionChecker.isAdmin(systemAdminUser), isTrue);
      });

      test('returns true for company admin', () {
        expect(PermissionChecker.isAdmin(companyAdminUser), isTrue);
      });

      test('returns false for non-admin roles', () {
        expect(PermissionChecker.isAdmin(accountantUser), isFalse);
        expect(PermissionChecker.isAdmin(viewerUser), isFalse);
      });
    });

    group('canAccessCompany', () {
      test('system admin can access any company', () {
        expect(
          PermissionChecker.canAccessCompany(systemAdminUser, 'company-1'),
          isTrue,
        );
        expect(
          PermissionChecker.canAccessCompany(systemAdminUser, 'company-2'),
          isTrue,
        );
        expect(
          PermissionChecker.canAccessCompany(systemAdminUser, null),
          isTrue,
        );
      });

      test('regular user can only access their own company', () {
        expect(
          PermissionChecker.canAccessCompany(companyAdminUser, 'company-1'),
          isTrue,
        );
        expect(
          PermissionChecker.canAccessCompany(companyAdminUser, 'company-2'),
          isFalse,
        );
      });

      test('regular user cannot access null company', () {
        expect(
          PermissionChecker.canAccessCompany(companyAdminUser, null),
          isFalse,
        );
      });
    });

    group('canPerformAction', () {
      test('returns true when user has permission and company access', () {
        expect(
          PermissionChecker.canPerformAction(
            companyAdminUser,
            Permission.createUsers,
            companyId: 'company-1',
          ),
          isTrue,
        );
      });

      test('returns false when user has permission but no company access', () {
        expect(
          PermissionChecker.canPerformAction(
            companyAdminUser,
            Permission.createUsers,
            companyId: 'company-2',
          ),
          isFalse,
        );
      });

      test('returns false when user lacks permission', () {
        expect(
          PermissionChecker.canPerformAction(
            viewerUser,
            Permission.createUsers,
            companyId: 'company-1',
          ),
          isFalse,
        );
      });

      test('returns true when no company check needed', () {
        expect(
          PermissionChecker.canPerformAction(
            companyAdminUser,
            Permission.viewUsers,
          ),
          isTrue,
        );
      });

      test('system admin can perform action on any company', () {
        expect(
          PermissionChecker.canPerformAction(
            systemAdminUser,
            Permission.createUsers,
            companyId: 'company-1',
          ),
          isTrue,
        );
        expect(
          PermissionChecker.canPerformAction(
            systemAdminUser,
            Permission.createUsers,
            companyId: 'company-2',
          ),
          isTrue,
        );
      });
    });
  });
}
