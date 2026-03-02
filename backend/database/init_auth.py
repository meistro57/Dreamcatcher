"""
Database initialization script for authentication system.
Creates default roles and seeds a default development user.
"""

import os
import logging
from database import get_db
from services.auth_service import AuthService, RoleCRUD

logger = logging.getLogger(__name__)


def init_auth_system():
    """Initialize authentication system with default roles and optional seeded users."""
    try:
        with get_db() as db:
            # Initialize services
            secret_key = os.getenv("SECRET_KEY")
            if not secret_key:
                raise RuntimeError("SECRET_KEY environment variable is required")
            auth_service = AuthService(secret_key, db)
            role_crud = RoleCRUD(db)

            # Create default roles
            logger.info("Creating default roles...")
            role_crud.create_default_roles()

            # Seed a default local-development account unless explicitly disabled.
            # These can be overridden with env vars for custom local credentials.
            is_development = os.getenv("ENVIRONMENT", "development") == "development"
            disable_default_dev_user = os.getenv("DISABLE_DEFAULT_DEV_USER", "false").lower() == "true"
            if is_development and not disable_default_dev_user:
                dev_email = os.getenv("DEFAULT_DEV_USER_EMAIL", "user@dreamcatcher.local")
                dev_username = os.getenv("DEFAULT_DEV_USER_USERNAME", "user")
                dev_password = os.getenv("DEFAULT_DEV_USER_PASSWORD", "password")
                dev_full_name = os.getenv("DEFAULT_DEV_USER_FULL_NAME", "Default User")
                enforce_default_dev_credentials = os.getenv(
                    "ENFORCE_DEFAULT_DEV_CREDENTIALS",
                    "true"
                ).lower() == "true"

                dev_user = auth_service.get_user_by_email(dev_email)

                if not dev_user:
                    logger.info("Creating default development user")
                    dev_user = auth_service.create_user(
                        email=dev_email,
                        username=dev_username,
                        full_name=dev_full_name,
                        password=dev_password,
                        roles=["user"]
                    )
                    dev_user.is_verified = True
                    db.commit()
                    logger.info("Default development user created")
                elif enforce_default_dev_credentials:
                    logger.info("Synchronizing default development user credentials")
                    updated = False

                    normalized_username = dev_username.lower()
                    if dev_user.username != normalized_username:
                        dev_user.username = normalized_username
                        updated = True

                    if dev_user.full_name != dev_full_name:
                        dev_user.full_name = dev_full_name
                        updated = True

                    if not auth_service.pwd_context.verify(dev_password, dev_user.password_hash):
                        dev_user.password_hash = auth_service.pwd_context.hash(dev_password)
                        updated = True

                    if not dev_user.is_active:
                        dev_user.is_active = True
                        updated = True

                    if not dev_user.is_verified:
                        dev_user.is_verified = True
                        updated = True

                    if updated:
                        db.commit()
                        logger.info("Default development user synchronized")

            logger.info("Authentication system initialized successfully")

    except Exception as e:
        logger.error(f"Authentication system initialization failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_auth_system()
