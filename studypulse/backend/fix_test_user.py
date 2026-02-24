"""Fix test user login credentials."""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash, verify_password


async def fix_test_user():
    async with AsyncSessionLocal() as session:
        # Check existing test user
        result = await session.execute(select(User).where(User.email == 'test@studypulse.com'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Found test user: {user.email}")
            print(f"Current hash: {user.hashed_password[:50]}...")
            
            # Update password
            new_password = 'testpassword123'
            user.hashed_password = get_password_hash(new_password)
            await session.commit()
            await session.refresh(user)
            
            print(f"New hash: {user.hashed_password[:50]}...")
            
            # Verify
            if verify_password(new_password, user.hashed_password):
                print("[OK] Password verification SUCCESS!")
            else:
                print("[ERROR] Password verification FAILED!")
            
            print('\nTest user credentials:')
            print('Email: test@studypulse.com')
            print('Password: testpassword123')
        else:
            print("Test user not found, creating...")
            user = User(
                email='test@studypulse.com',
                name='Test User',
                hashed_password=get_password_hash('testpassword123'),
                is_active=True,
                total_stars=0
            )
            session.add(user)
            await session.commit()
            print('[OK] Test user created!')
            print('Email: test@studypulse.com')
            print('Password: testpassword123')


if __name__ == "__main__":
    asyncio.run(fix_test_user())
