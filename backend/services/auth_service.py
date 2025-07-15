"""
Authentication service for Dreamcatcher
Handles user authentication, JWT tokens, and session management
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.models import User, Role, UserSession
from database.crud import BaseCRUD


class AuthenticationError(Exception):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username/password"""
    pass


class AccountLockedError(AuthenticationError):
    """Account is locked due to too many failed attempts"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid"""
    pass


class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    def __init__(self, secret_key: str, db: Session):
        self.secret_key = secret_key
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 15
        
    def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
        roles: List[str] = None
    ) -> User:
        """Create a new user account"""
        if self.get_user_by_email(email):
            raise ValueError("Email already registered")
        
        if self.get_user_by_username(username):
            raise ValueError("Username already taken")
        
        # Hash password
        password_hash = self.pwd_context.hash(password)
        
        # Create user
        user = User(
            email=email.lower(),
            username=username.lower(),
            full_name=full_name,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
            email_verification_token=secrets.token_urlsafe(32),
            email_verification_expires=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(user)
        self.db.flush()
        
        # Add default role if no roles specified
        if not roles:
            roles = ["user"]
        
        for role_name in roles:
            role = self.db.query(Role).filter(Role.name == role_name).first()
            if role:
                user.roles.append(role)
        
        self.db.commit()
        return user
    
    def authenticate_user(self, email_or_username: str, password: str) -> User:
        """Authenticate user with email/username and password"""
        user = self.get_user_by_email_or_username(email_or_username)
        
        if not user:
            raise InvalidCredentialsError("Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AccountLockedError("Account is temporarily locked")
        
        # Check if account is active
        if not user.is_active:
            raise InvalidCredentialsError("Account is deactivated")
        
        # Verify password
        if not self.pwd_context.verify(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            
            self.db.commit()
            raise InvalidCredentialsError("Invalid credentials")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.login_count += 1
        
        self.db.commit()
        return user
    
    def create_access_token(self, user: User, device_info: Dict = None) -> Dict[str, Any]:
        """Create JWT access token and refresh token"""
        now = datetime.utcnow()
        access_expire = now + timedelta(minutes=self.access_token_expire_minutes)
        refresh_expire = now + timedelta(days=self.refresh_token_expire_days)
        
        # Access token payload
        access_payload = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "roles": [role.name for role in user.roles],
            "iat": now,
            "exp": access_expire,
            "type": "access"
        }
        
        # Refresh token payload
        refresh_payload = {
            "sub": user.id,
            "iat": now,
            "exp": refresh_expire,
            "type": "refresh"
        }
        
        # Create tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            token_hash=hashlib.sha256(access_token.encode()).hexdigest(),
            refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            device_info=device_info or {},
            expires_at=access_expire,
            is_active=True
        )
        
        self.db.add(session)
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "roles": [role.name for role in user.roles],
                "is_verified": user.is_verified
            }
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "refresh":
                raise TokenInvalidError("Invalid token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise TokenInvalidError("Invalid token payload")
            
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise TokenInvalidError("User not found or inactive")
            
            # Verify refresh token in session
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            session = self.db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.refresh_token_hash == token_hash,
                    UserSession.is_active == True
                )
            ).first()
            
            if not session:
                raise TokenInvalidError("Invalid refresh token")
            
            # Create new access token
            return self.create_access_token(user, session.device_info)
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise TokenInvalidError("Invalid refresh token")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "access":
                raise TokenInvalidError("Invalid token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise TokenInvalidError("Invalid token payload")
            
            # Verify token in session
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            session = self.db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.token_hash == token_hash,
                    UserSession.is_active == True
                )
            ).first()
            
            if not session:
                raise TokenInvalidError("Token not found in active sessions")
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            raise TokenInvalidError("Invalid token")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a specific token"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            session = self.db.query(UserSession).filter(
                UserSession.token_hash == token_hash
            ).first()
            
            if session:
                session.is_active = False
                self.db.commit()
                return True
            
            return False
            
        except Exception:
            return False
    
    def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        count = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).update({"is_active": False})
        
        self.db.commit()
        return count
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def get_user_by_email_or_username(self, email_or_username: str) -> Optional[User]:
        """Get user by email or username"""
        search_term = email_or_username.lower()
        return self.db.query(User).filter(
            or_(User.email == search_term, User.username == search_term)
        ).first()
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not self.pwd_context.verify(current_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = self.pwd_context.hash(new_password)
        user.updated_at = datetime.utcnow()
        
        # Revoke all existing sessions
        self.revoke_user_sessions(user_id)
        
        self.db.commit()
        return True
    
    def reset_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password (admin function)"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = self.pwd_context.hash(new_password)
        user.updated_at = datetime.utcnow()
        
        # Revoke all existing sessions
        self.revoke_user_sessions(user_id)
        
        self.db.commit()
        return True
    
    def verify_email(self, token: str) -> bool:
        """Verify user email with token"""
        user = self.db.query(User).filter(
            and_(
                User.email_verification_token == token,
                User.email_verification_expires > datetime.utcnow(),
                User.is_verified == False
            )
        ).first()
        
        if user:
            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            user.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission"""
        for role in user.roles:
            if role.permissions and permission in role.permissions:
                return role.permissions[permission]
        return False
    
    def has_role(self, user: User, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in user.roles)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        count = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).update({"is_active": False})
        
        self.db.commit()
        return count


class UserCRUD(BaseCRUD):
    """CRUD operations for User model"""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def get_active_users(self) -> List[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.is_active == True).all()
    
    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by name, email, or username"""
        search_term = f"%{query.lower()}%"
        return self.db.query(User).filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        ).limit(limit).all()


class RoleCRUD(BaseCRUD):
    """CRUD operations for Role model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Role)
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def create_default_roles(self) -> None:
        """Create default system roles"""
        default_roles = [
            {
                "name": "admin",
                "description": "System administrator with full access",
                "permissions": {
                    "user.create": True,
                    "user.read": True,
                    "user.update": True,
                    "user.delete": True,
                    "idea.create": True,
                    "idea.read": True,
                    "idea.update": True,
                    "idea.delete": True,
                    "agent.manage": True,
                    "system.manage": True
                }
            },
            {
                "name": "user",
                "description": "Standard user with basic access",
                "permissions": {
                    "idea.create": True,
                    "idea.read": True,
                    "idea.update": True,
                    "idea.delete": False,
                    "profile.update": True
                }
            },
            {
                "name": "guest",
                "description": "Guest user with read-only access",
                "permissions": {
                    "idea.read": True
                }
            }
        ]
        
        for role_data in default_roles:
            if not self.get_by_name(role_data["name"]):
                role = Role(**role_data)
                self.db.add(role)
        
        self.db.commit()