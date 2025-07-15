#!/usr/bin/env python3
"""
Test script for authentication system
"""

import os
import sys
import tempfile
import sqlite3
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test with in-memory SQLite
TEST_DB_URL = "sqlite:///:memory:"

def test_auth_system():
    """Test the authentication system"""
    print("🔐 Testing Dreamcatcher Authentication System...")
    
    try:
        # Set up test environment
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
        os.environ["DATABASE_URL"] = TEST_DB_URL
        
        # Import after setting environment variables
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base, User, Role, UserSession
        from services.auth_service import AuthService, RoleCRUD
        
        # Create test database
        engine = create_engine(TEST_DB_URL)
        Base.metadata.create_all(engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialize services
        auth_service = AuthService("test-secret-key", db)
        role_crud = RoleCRUD(db)
        
        print("✅ Database and services initialized")
        
        # Test 1: Create default roles
        print("\n📝 Test 1: Creating default roles...")
        role_crud.create_default_roles()
        
        roles = db.query(Role).all()
        print(f"✅ Created {len(roles)} default roles:")
        for role in roles:
            print(f"   - {role.name}: {role.description}")
        
        # Test 2: Create user
        print("\n👤 Test 2: Creating user account...")
        user = auth_service.create_user(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="password123",
            roles=["user"]
        )
        
        print(f"✅ Created user: {user.email} ({user.username})")
        print(f"   - ID: {user.id}")
        print(f"   - Roles: {[role.name for role in user.roles]}")
        print(f"   - Active: {user.is_active}")
        print(f"   - Verified: {user.is_verified}")
        
        # Test 3: Authentication
        print("\n🔑 Test 3: Testing authentication...")
        
        # Test successful login
        try:
            auth_user = auth_service.authenticate_user("test@example.com", "password123")
            print(f"✅ Authentication successful: {auth_user.email}")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
        
        # Test failed login
        try:
            auth_service.authenticate_user("test@example.com", "wrongpassword")
            print("❌ Authentication should have failed")
            return False
        except Exception as e:
            print(f"✅ Authentication correctly failed: {e}")
        
        # Test 4: JWT tokens
        print("\n🎫 Test 4: Testing JWT tokens...")
        
        token_data = auth_service.create_access_token(user)
        print(f"✅ Created access token")
        print(f"   - Token type: {token_data['token_type']}")
        print(f"   - Expires in: {token_data['expires_in']} seconds")
        print(f"   - User data: {token_data['user']['email']}")
        
        # Test token verification
        try:
            payload = auth_service.verify_token(token_data['access_token'])
            print(f"✅ Token verification successful")
            print(f"   - User ID: {payload['sub']}")
            print(f"   - Roles: {payload['roles']}")
        except Exception as e:
            print(f"❌ Token verification failed: {e}")
            return False
        
        # Test 5: Permissions
        print("\n🔒 Test 5: Testing permissions...")
        
        # Test user permissions
        has_create = auth_service.has_permission(user, "idea.create")
        has_delete = auth_service.has_permission(user, "idea.delete")
        has_admin = auth_service.has_role(user, "admin")
        
        print(f"✅ Permission checks:")
        print(f"   - Can create ideas: {has_create}")
        print(f"   - Can delete ideas: {has_delete}")
        print(f"   - Has admin role: {has_admin}")
        
        # Test 6: Session management
        print("\n💾 Test 6: Testing session management...")
        
        sessions = db.query(UserSession).filter(UserSession.user_id == user.id).all()
        print(f"✅ User has {len(sessions)} active sessions")
        
        # Test token revocation
        revoked = auth_service.revoke_token(token_data['access_token'])
        print(f"✅ Token revocation: {revoked}")
        
        # Test 7: Password operations
        print("\n🔐 Test 7: Testing password operations...")
        
        # Test password change
        changed = auth_service.change_password(user.id, "password123", "newpassword123")
        print(f"✅ Password change: {changed}")
        
        # Test login with new password
        try:
            auth_user = auth_service.authenticate_user("test@example.com", "newpassword123")
            print(f"✅ Login with new password successful")
        except Exception as e:
            print(f"❌ Login with new password failed: {e}")
            return False
        
        # Clean up
        db.close()
        
        print("\n🎉 All authentication tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_auth_system()
    sys.exit(0 if success else 1)