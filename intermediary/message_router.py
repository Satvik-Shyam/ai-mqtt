"""
Message Router for the AI-IoT Intermediary

This module handles routing messages between agents and devices.
It implements the core routing logic for the A2A protocol.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Set
import redis.asyncio as redis
import os

class MessageRouter:
    """Routes messages between agents and devices"""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = None
        self.running = False
        self.agent_connections = {}  # agent_id -> connection info
        self.agent_subscriptions = {}  # topic -> set of agent_ids
        
    async def start(self):
        """Start the message router"""
        self.redis = await redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        self.running = True
        asyncio.create_task(self.process_message_queue())
        print(f"Message Router started with Redis at {self.redis_host}:{self.redis_port}")
        
    async def stop(self):
        """Stop the message router"""
        self.running = False
        if self.redis:
            await self.redis.close()
            
    async def register_agent(self, agent_id: str, connection_info: Dict[str, Any]):
        """Register an agent with the message router"""
        self.agent_connections[agent_id] = connection_info
        
        # Store in Redis for persistence
        await self.redis.hset(
            "agent_connections",
            agent_id,
            json.dumps(connection_info)
        )
        
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the message router"""
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]
            
        # Remove from Redis
        await self.redis.hdel("agent_connections", agent_id)
        
        # Remove from all subscriptions
        for topic, subscribers in self.agent_subscriptions.items():
            if agent_id in subscribers:
                subscribers.remove(agent_id)
                
    async def subscribe_agent(self, agent_id: str, topic: str):
        """Subscribe an agent to a topic"""
        if topic not in self.agent_subscriptions:
            self.agent_subscriptions[topic] = set()
            
        self.agent_subscriptions[topic].add(agent_id)
        
        # Store in Redis
        await self.redis.sadd(f"topic:{topic}:subscribers", agent_id)
        
    async def unsubscribe_agent(self, agent_id: str, topic: str):
        """Unsubscribe an agent from a topic"""
        if topic in self.agent_subscriptions and agent_id in self.agent_subscriptions[topic]:
            self.agent_subscriptions[topic].remove(agent_id)
            
            # Remove from Redis
            await self.redis.srem(f"topic:{topic}:subscribers", agent_id)
            
    async def route_a2a_message(self, source_agent_id: str, target_agent_id: str, message: Dict[str, Any]):
        """Route a message from one agent to another"""
        # Add message to queue
        message_data = {
            "source_agent_id": source_agent_id,
            "target_agent_id": target_agent_id,
            "message": message,
            "timestamp": time.time()
        }
        
        await self.redis.lpush(
            "agent_message_queue",
            json.dumps(message_data)
        )
        
        # If target agent has a WebSocket connection, deliver immediately
        # This would be implemented with a WebSocket manager
        
    async def route_device_data(self, device_type: str, device_id: str, data: Dict[str, Any]):
        """Route device data to subscribed agents"""
        topic = f"devices/{device_type}/{device_id}"
        
        # Find all agents subscribed to this topic
        subscribers = set()
        
        # Direct subscribers
        if topic in self.agent_subscriptions:
            subscribers.update(self.agent_subscriptions[topic])
            
        # Wildcard subscribers (devices/+/+)
        wildcard_topic = f"devices/{device_type}/+"
        if wildcard_topic in self.agent_subscriptions:
            subscribers.update(self.agent_subscriptions[wildcard_topic])
            
        # All devices wildcard (devices/+/+)
        all_devices_topic = "devices/+/+"
        if all_devices_topic in self.agent_subscriptions:
            subscribers.update(self.agent_subscriptions[all_devices_topic])
            
        # Route data to all subscribers
        for agent_id in subscribers:
            message_data = {
                "source_type": "device",
                "source_id": device_id,
                "target_agent_id": agent_id,
                "data": data,
                "timestamp": time.time()
            }
            
            await self.redis.lpush(
                "device_data_queue",
                json.dumps(message_data)
            )
            
    async def process_message_queue(self):
        """Process the message queue"""
        while self.running:
            try:
                # Process agent-to-agent messages
                message_data = await self.redis.brpop("agent_message_queue", timeout=1)
                if message_data:
                    _, message_json = message_data
                    message = json.loads(message_json)
                    await self.deliver_a2a_message(message)
                    
                # Process device data messages
                device_data = await self.redis.brpop("device_data_queue", timeout=1)
                if device_data:
                    _, data_json = device_data
                    data = json.loads(data_json)
                    await self.deliver_device_data(data)
                    
            except Exception as e:
                print(f"Error processing message queue: {e}")
                await asyncio.sleep(1)  # Avoid tight loop on error
                
    async def deliver_a2a_message(self, message_data: Dict[str, Any]):
        """Deliver an agent-to-agent message"""
        target_agent_id = message_data.get("target_agent_id")
        
        # In a real implementation, this would deliver via WebSocket or other mechanism
        # For this example, we'll just log it
        print(f"Delivering message to agent {target_agent_id}")
        
        # Store message in history
        await self.redis.lpush(
            f"agent:{target_agent_id}:messages",
            json.dumps(message_data)
        )
        
        # Trim history to last 100 messages
        await self.redis.ltrim(f"agent:{target_agent_id}:messages", 0, 99)
        
    async def deliver_device_data(self, data: Dict[str, Any]):
        """Deliver device data to an agent"""
        target_agent_id = data.get("target_agent_id")
        
        # In a real implementation, this would deliver via WebSocket or other mechanism
        # For this example, we'll just log it
        print(f"Delivering device data to agent {target_agent_id}")
        
        # Store data in history
        await self.redis.lpush(
            f"agent:{target_agent_id}:device_data",
            json.dumps(data)
        )
        
        # Trim history to last 100 data points
        await self.redis.ltrim(f"agent:{target_agent_id}:device_data", 0, 99)
