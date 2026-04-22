# backend/auth/auth_service.py

import bcrypt
from typing import Optional, Tuple
try:
    from .jwt_handler import JWTHandler
except ImportError:
    from jwt_handler import JWTHandler

class User:
    """Simple user model (will be replaced with database model later)"""
    def __init__(self, id: int, email: str, password_hash: str, first_name: str = None, last_name: str = None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name


class AuthService:
    """Handles user authentication (signup, login, password management)"""
    
    def __init__(self, secret_key: str):
        """
        Initialize authentication service
        
        Args:
            secret_key: Secret key for JWT tokens
        """
        self.jwt_handler = JWTHandler(secret_key)
        # In-memory user storage (will be replaced with database later)
        self.users = {}  # {email: User}
        self.next_user_id = 1
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def signup(
        self, 
        email: str, 
        password: str, 
        first_name: str = None, 
        last_name: str = None
    ) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Create a new user account
        
        Args:
            email: User's email
            password: User's password (plain text)
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            Tuple of (success, error_message, user)
        """
        # Validate email
        if not email or '@' not in email:
            return False, "Invalid email address", None
        
        # Validate password
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters", None
        
        # Check if user already exists
        if email.lower() in self.users:
            return False, "Email already registered", None
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        user = User(
            id=self.next_user_id,
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        
        # Save user
        self.users[email.lower()] = user
        self.next_user_id += 1
        
        return True, None, user
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Login a user
        
        Args:
            email: User's email
            password: User's password (plain text)
            
        Returns:
            Tuple of (success, error_message, token)
        """
        # Find user
        user = self.users.get(email.lower())
        if not user:
            return False, "Invalid email or password", None
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            return False, "Invalid email or password", None
        
        # Generate token
        token = self.jwt_handler.create_token(user.id)
        
        return True, None, token
    
    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify a token and return the user
        
        Args:
            token: JWT token
            
        Returns:
            User if token is valid, None otherwise
        """
        user_id = self.jwt_handler.get_user_id_from_token(token)
        if not user_id:
            return None
        
        # Find user by ID
        for user in self.users.values():
            if user.id == user_id:
                return user
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.users.get(email.lower())


