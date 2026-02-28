"""
Database initialization script for authentication system
Creates default roles and optional seeded users
"""

import os
import asyncio
import logging
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import AuthService, RoleCRUD
from database.models import Role, User

logger = logging.getLogger(__name__)


def init_auth_system():
    """Initialize authentication system with default roles and optional seeded users."""
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize services
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise RuntimeError("SECRET_KEY environment variable is required")
        auth_service = AuthService(secret_key, db)
        role_crud = RoleCRUD(db)
        
        # Create default roles
        logger.info("Creating default roles...")
        role_crud.create_default_roles()
        
        logger.info("Skipping automatic admin user creation; create admin explicitly via API/CLI")

        # Optionally seed test user in development when explicitly enabled
        should_seed_test_user = os.getenv("SEED_TEST_USER", "false").lower() == "true"
        if os.getenv("ENVIRONMENT", "development") == "development" and should_seed_test_user:
            test_user = auth_service.get_user_by_email("user@dreamcatcher.local")
            
            if not test_user:
                logger.info("Creating test user for development (SEED_TEST_USER=true)")
                test_user = auth_service.create_user(
                    email="user@dreamcatcher.local",
                    username="testuser",
                    full_name="Test User",
                    password="user123",
                    roles=["user"]
                )
                test_user.is_verified = True
                db.commit()
                logger.info("Test user created for development")
        
        logger.info("Authentication system initialized successfully")
        
    except Exception as e:
        logger.error(f"Authentication system initialization failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_auth_system()