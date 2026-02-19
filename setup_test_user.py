import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.app.db.session import get_db_manager
from src.app.repositories.user_repository import UserRepository
from src.app.models.user import User

async def main():
    db_manager = get_db_manager()
    async with db_manager.session_factory() as db:
        repo = UserRepository(db)
        phone = "9999999999"
        
        print(f"Checking user with phone {phone}...")
        user = await repo.get_by_phone(phone)
        
        if user:
            print(f"User found: ID={user.id}, Email={user.email}, Phone={user.phone}")
            
            # Update email if missing
            if not user.email:
                print("Updating user email to 'test@example.com'...")
                user.email = "test@example.com"
                await db.commit()
                await db.refresh(user)
                print(f"User updated: Email={user.email}")
            else:
                print("User already has email.")
        else:
            print("User not found. Creating...")
            user = await repo.create(
                phone=phone,
                email="test@example.com",
                role="user",
                is_active=True
            )
            print(f"User created: ID={user.id}")

if __name__ == "__main__":
    asyncio.run(main())
