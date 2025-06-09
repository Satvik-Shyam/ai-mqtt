import asyncio
import uuid
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel
import logging

class AgentMessage(BaseModel):
    agent_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, agent_type: str, intermediary_url: str):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.intermediary_url = intermediary_url
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")
        self.message_handlers = {}
        self._running = False
        
    async def start(self):
        """Start the agent"""
        self._running = True
        await self.register_with_intermediary()
        asyncio.create_task(self.run())
        
    async def stop(self):
        """Stop the agent"""
        self._running = False
        
    async def register_with_intermediary(self):
        """Register agent with the intermediary"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.intermediary_url}/agents/register",
                json={
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "agent_type": self.agent_type,
                    "capabilities": self.get_capabilities()
                }
            )
            self.logger.info(f"Registered with intermediary: {response.status_code}")
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage):
        """Process incoming message"""
        pass
    
    async def send_to_agent(self, target_agent_id: str, message_type: str, payload: Dict[str, Any]):
        """Send message to another agent via A2A protocol"""
        message = AgentMessage(
            agent_id=self.agent_id,
            message_type=message_type,
            payload=payload,
            timestamp=time.time()
        )
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.intermediary_url}/agents/message",
                json={
                    "source_agent_id": self.agent_id,
                    "target_agent_id": target_agent_id,
                    "message": message.dict()
                }
            )
    
    async def query_iot_data(self, device_type: str, query_params: Dict[str, Any]):
        """Query IoT data through intermediary"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.intermediary_url}/iot/query",
                json={
                    "agent_id": self.agent_id,
                    "device_type": device_type,
                    "query_params": query_params
                }
            )
            return response.json()
    
    async def control_iot_device(self, device_id: str, command: Dict[str, Any]):
        """Send control command to IoT device"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.intermediary_url}/iot/control",
                json={
                    "agent_id": self.agent_id,
                    "device_id": device_id,
                    "command": command
                }
            )
            return response.json()
