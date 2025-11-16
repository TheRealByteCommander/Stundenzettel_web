#!/usr/bin/env python3
"""
Reset Admin User Script
Resets the admin user's 2FA to allow setup again.
"""
import asyncio
import sys
import os

# Add parent directory to path to import server modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from server import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_NAME,
    get_password_hash,
    mongo_url,
    db
)
import pyotp
import uuid

async def reset_admin_user():
    """Reset admin user: new secret, disable 2FA, reset password"""
    
    target_email = DEFAULT_ADMIN_EMAIL.strip().lower()
    admin = await db.users.find_one({"email": target_email})
    
    if not admin:
        print(f"Admin user {target_email} not found. Creating new admin user...")
        two_fa_secret = pyotp.random_base32()
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": target_email,
            "name": DEFAULT_ADMIN_NAME,
            "role": "admin",
            "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
            "two_fa_secret": two_fa_secret,
            "two_fa_enabled": False,
            "is_admin": True,
            "weekly_hours": 40.0
        }
        await db.users.insert_one(admin_user)
        print(f"✓ Admin user created: {target_email} / {DEFAULT_ADMIN_PASSWORD}")
    else:
        print(f"Resetting admin user {target_email}...")
        two_fa_secret = pyotp.random_base32()
        await db.users.update_one(
            {"email": target_email},
            {
                "$set": {
                    "two_fa_secret": two_fa_secret,
                    "two_fa_enabled": False,
                    "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
                    "name": DEFAULT_ADMIN_NAME,
                    "role": "admin",
                    "is_admin": True
                }
            }
        )
        print(f"✓ Admin user reset: {target_email} / {DEFAULT_ADMIN_PASSWORD}")
        print(f"  New 2FA secret generated. User can now setup 2FA again.")

if __name__ == "__main__":
    try:
        asyncio.run(reset_admin_user())
        print("\n✓ Done! You can now login and setup 2FA.")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

