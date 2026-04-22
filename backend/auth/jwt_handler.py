# backend/auth/jwt_handler.py

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

class JWTHandler:
    """Handles JWT token creation and verification"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT handler
        
        Args:
            secret_key: Secret key for signing tokens (keep this secret!)
            algorithm: Hashing algorithm (HS256 is standard)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, user_id: int, expires_in_days: int = 7) -> str:
        """
        Create a JWT token for a user
        
        Args:
            user_id: The user's ID
            expires_in_days: How many days until token expires
            
        Returns:
            JWT token string
        """
        # Create payload with user info and expiration
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(days=expires_in_days),
            'iat': datetime.now(timezone.utc)  # Issued at
        }
        
        # Encode payload into JWT token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify a JWT token and extract payload
        
        Args:
            token: JWT token string
            
        Returns:
            Payload dict if valid, None if invalid/expired
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[int]:
        """
        Extract user ID from a token
        
        Args:
            token: JWT token string
            
        Returns:
            User ID if valid, None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get('user_id')
        return None


