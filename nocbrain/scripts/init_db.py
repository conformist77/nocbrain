#!/usr/bin/env python3
"""
Initialize NOCBrain database with default user
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.db import AsyncSessionLocal
from app.models import User
from app.auth import get_password_hash


async def create_default_user():
    """Create default admin user"""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Default admin user already exists")
            return
        
        # Create default user
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123")
        )
        
        db.add(admin_user)
        await db.commit()
        
        print("Created default admin user:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Please change the password after first login!")


if __name__ == "__main__":
    asyncio.run(create_default_user())
