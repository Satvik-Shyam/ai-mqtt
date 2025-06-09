"""
Security Manager for the AI-IoT Intermediary

This module handles security-related functionality:
- Authentication and authorization
- Access control for agents and devices
- Encryption/decryption of sensitive data
"""

import time
import json
import hashlib
import os
import jwt
from typing import Dict, Any, List, Optional
import redis.asyncio as redis

class SecurityManager:
    """Manages security for the intermediary"""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = None
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-key")  # In production, use a secure secret
        self.token_expiry = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize the security manager"""
        self.redis = await redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        
    async def close(self):
        """Close connections"""
        if self.redis:
            await self.redis.close()
    
    async def authenticate_agent(self, agent_id: str, credentials: Dict[str, Any]) -> bool:
        """Authenticate an agent"""
        # In a real system, this would validate credentials against a database
        # For this example, we'll accept any credentials in development mode
        
        # Store agent info
        await self.redis.hset(
            "authenticated_agents",
            agent_id,
            json.dumps({
                "authenticated_at": time.time(),
                "agent_type": credentials.get("agent_type", "unknown")
            })
        )
        
        return True
    
    async def generate_agent_token(self, agent_id: str, agent_type: str) -> str:
        """Generate a JWT token for an agent"""
        payload = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "exp": int(time.time()) + self.token_expiry,
            "iat": int(time.time())
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    async def validate_agent_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an agent token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check if agent is still authenticated
            agent_info = await self.redis.hget("authenticated_agents", payload["agent_id"])
            if not agent_info:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def check_agent_permission(self, agent_id: str, resource_type: str, 
                                   resource_id: str, action: str) -> bool:
        """Check if an agent has permission to perform an action on a resource"""
        # Get agent type
        agent_info_json = await self.redis.hget("authenticated_agents", agent_id)
        if not agent_info_json:
            return False
            
        agent_info = json.loads(agent_info_json)
        agent_type = agent_info.get("agent_type", "unknown")
        
        # In a real system, this would check against a permissions database
        # For this example, we'll implement some basic rules
        
        # Control agents can control devices
        if resource_type == "device" and action == "control" and agent_type == "control":
            return True
            
        # Monitoring agents can read device data
        if resource_type == "device" and action == "read" and agent_type == "monitoring":
            return True
            
        # Analytics agents can read device data
        if resource_type == "device" and action == "read" and agent_type == "analytics":
            return True
            
        # Default deny
        return False
    
    async def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data (placeholder implementation)"""
        # In a real system, this would use proper encryption
        # For this example, we'll just mark the data as "encrypted"
        return {
            "encrypted": True,
            "data": data
        }
    
    async def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data (placeholder implementation)"""
        # In a real system, this would use proper decryption
        # For this example, we'll just return the data
        if encrypted_data.get("encrypted"):
            return encrypted_data.get("data", {})
        return encrypted_data
    
    async def hash_password(self, password: str) -> str:
        """Hash a password"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt.hex() + ':' + key.hex()
    
    async def verify_password(self, stored_hash: str, password: str) -> bool:
        """Verify a password against a stored hash"""
        salt_hex, key_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return key == stored_key
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log a security event"""
        event = {
            "event_type": event_type,
            "timestamp": time.time(),
            "details": details
        }
        
        # Store in Redis
        await self.redis.lpush("security_events", json.dumps(event))
        
        # Keep only the last 1000 events
        await self.redis.ltrim("security_events", 0, 999)
