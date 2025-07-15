"""
Database initialization script for authentication system
Creates default roles and admin user
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
    """Initialize authentication system with default roles and admin user"""
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize services
        secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
        auth_service = AuthService(secret_key, db)
        role_crud = RoleCRUD(db)
        
        # Create default roles
        logger.info("Creating default roles...")
        role_crud.create_default_roles()
        
        # Check if admin user exists
        admin_user = auth_service.get_user_by_email("admin@dreamcatcher.local")
        
        if not admin_user:
            # Create admin user
            admin_email = os.getenv("ADMIN_EMAIL", "admin@dreamcatcher.local")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin_name = os.getenv("ADMIN_NAME", "System Administrator")
            
            logger.info(f"Creating admin user: {admin_email}")
            
            admin_user = auth_service.create_user(
                email=admin_email,
                username=admin_username,
                full_name=admin_name,
                password=admin_password,
                roles=["admin"]
            )
            
            # Mark admin as verified
            admin_user.is_verified = True
            db.commit()
            
            logger.info("Admin user created successfully")
            
            # Security warning for default credentials
            if admin_password == "admin123":
                logger.warning("⚠️  WARNING: Default admin password is being used!")
                logger.warning("⚠️  Please change the admin password immediately!")
                logger.warning("⚠️  Set ADMIN_PASSWORD environment variable to use a secure password")
        else:
            logger.info("Admin user already exists")
        
        # Create sample regular user if in development
        if os.getenv("ENVIRONMENT", "development") == "development":
            test_user = auth_service.get_user_by_email("user@dreamcatcher.local")
            
            if not test_user:
                logger.info("Creating test user for development")
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