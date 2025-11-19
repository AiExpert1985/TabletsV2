"""Diagnostic script to test login functionality."""
import asyncio
import sys
from sqlalchemy import select
from features.auth.models import User
from core.database import AsyncSessionLocal


async def test_database():
    """Test if database is accessible."""
    print("Testing database connection...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                print(f"✓ Database OK - Found user: {user.phone_number}")

                # Check if company relationship works
                if user.company_id:
                    print(f"  User has company_id: {user.company_id}")
                    try:
                        company = user.company
                        print(f"  Company access: {company.name if company else 'NULL'}")
                    except Exception as e:
                        print(f"  ✗ Error accessing company: {e}")
                else:
                    print(f"  User is system admin (no company)")

                return True
            else:
                print("✗ No users found in database")
                return False
    except Exception as e:
        print(f"✗ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_login_flow():
    """Test the login flow."""
    print("\nTesting login flow...")
    try:
        from features.auth.repository import RefreshTokenRepository
        from features.users.repository import UserRepository
        from features.auth.auth_services import AuthService

        async with AsyncSessionLocal() as session:
            # Get first user
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("✗ No users to test with")
                return False

            print(f"Testing with user: {user.phone_number}")

            # Create services
            user_repo = UserRepository(session)
            refresh_token_repo = RefreshTokenRepository(session)
            auth_service = AuthService(user_repo, refresh_token_repo)

            # Try to build user response
            print("Building user response...")
            from features.users.dependencies import build_user_response

            # Reload user with eager loading
            user = await user_repo.get_by_id(str(user.id))

            try:
                user_response = build_user_response(user)
                print(f"✓ User response built successfully")
                print(f"  Permissions: {len(user_response.permissions)} permissions")
                return True
            except Exception as e:
                print(f"✗ Error building user response: {e}")
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"✗ Login flow error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("BACKEND DIAGNOSTIC TEST")
    print("=" * 60)

    db_ok = await test_database()
    if not db_ok:
        print("\n✗ Database test failed - cannot continue")
        sys.exit(1)

    login_ok = await test_login_flow()
    if not login_ok:
        print("\n✗ Login flow test failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nIf tests pass but login still times out, the issue is likely:")
    print("1. Network/firewall blocking the connection")
    print("2. Server not actually running on the expected port")
    print("3. Client sending requests to wrong URL")


if __name__ == "__main__":
    asyncio.run(main())
