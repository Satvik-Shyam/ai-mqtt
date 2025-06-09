"""
Agent-to-Agent (A2A) Protocol Implementation

This module defines the protocol for communication between AI agents in the system.
It provides standardized message formats and handling mechanisms.
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class A2AMessage(BaseModel):
    """Base message format for Agent-to-Agent communication"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent_id: str
    target_agent_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    ttl: int = 60  # Time-to-live in seconds

class A2AProtocol:
    """Implementation of the Agent-to-Agent protocol"""
    
    def __init__(self):
        self.message_handlers = {}
        self.message_history = {}  # For tracking message chains
    
    def register_handler(self, message_type: str, handler_func):
        """Register a handler function for a specific message type"""
        self.message_handlers[message_type] = handler_func
    
    def create_message(self, source_agent_id: str, target_agent_id: str, 
                      message_type: str, payload: Dict[str, Any],
                      correlation_id: Optional[str] = None) -> A2AMessage:
        """Create a new A2A message"""
        return A2AMessage(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id
        )
    
    def create_response(self, original_message: A2AMessage, 
                       response_type: str, payload: Dict[str, Any]) -> A2AMessage:
        """Create a response to an existing message"""
        return A2AMessage(
            source_agent_id=original_message.target_agent_id,
            target_agent_id=original_message.source_agent_id,
            message_type=response_type,
            payload=payload,
            correlation_id=original_message.message_id
        )
    
    def serialize_message(self, message: A2AMessage) -> str:
        """Serialize message to JSON string"""
        return json.dumps(message.dict())
    
    def deserialize_message(self, message_str: str) -> A2AMessage:
        """Deserialize message from JSON string"""
        message_data = json.loads(message_str)
        return A2AMessage(**message_data)
    
    async def process_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Process an incoming message using registered handlers"""
        # Store in message history
        self.message_history[message.message_id] = {
            "message": message,
            "received_at": time.time()
        }
        
        # Check if we have a handler for this message type
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            response = await handler(message)
            
            # If handler returns a response, store it in history
            if response:
                self.message_history[response.message_id] = {
                    "message": response,
                    "received_at": time.time(),
                    "in_response_to": message.message_id
                }
            
            return response
        
        return None
    
    def get_message_chain(self, root_message_id: str) -> List[A2AMessage]:
        """Retrieve a chain of messages starting from a root message"""
        if root_message_id not in self.message_history:
            return []
        
        chain = [self.message_history[root_message_id]["message"]]
        
        # Find all messages in the chain
        for msg_id, msg_data in self.message_history.items():
            if msg_data.get("in_response_to") == root_message_id:
                # Add this message to the chain
                chain.append(msg_data["message"])
                
                # Recursively find responses to this message
                chain.extend(self.get_message_chain(msg_id))
        
        return chain
    
    def cleanup_old_messages(self, max_age_seconds: int = 3600):
        """Clean up old messages from history"""
        current_time = time.time()
        to_remove = []
        
        for msg_id, msg_data in self.message_history.items():
            age = current_time - msg_data["received_at"]
            if age > max_age_seconds:
                to_remove.append(msg_id)
        
        for msg_id in to_remove:
            del self.message_history[msg_id]
