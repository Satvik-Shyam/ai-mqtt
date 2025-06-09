from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import asyncio
import json
from .mqtt_handler import MQTTHandler
from .data_transformer import DataTransformer
from .message_router import MessageRouter

app = FastAPI(title="AI-IoT Intermediary")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
mqtt_handler = MQTTHandler()
data_transformer = DataTransformer()
message_router = MessageRouter()

# Store registered agents
registered_agents: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    await mqtt_handler.connect()
    await message_router.start()

@app.on_event("shutdown")
async def shutdown_event():
    await mqtt_handler.disconnect()
    await message_router.stop()

@app.post("/agents/register")
async def register_agent(agent_data: Dict[str, Any]):
    """Register a new AI agent"""
    agent_id = agent_data["agent_id"]
    registered_agents[agent_id] = agent_data
    
    # Setup agent-specific MQTT subscriptions if needed
    await mqtt_handler.subscribe(f"agents/{agent_id}/iot_data")
    
    return {"status": "registered", "agent_id": agent_id}

@app.post("/agents/message")
async def forward_agent_message(message_data: Dict[str, Any]):
    """Forward message between agents (A2A protocol)"""
    source_agent_id = message_data["source_agent_id"]
    target_agent_id = message_data["target_agent_id"]
    message = message_data["message"]
    
    if target_agent_id not in registered_agents:
        raise HTTPException(status_code=404, detail="Target agent not found")
    
    # Route message through message router
    await message_router.route_a2a_message(source_agent_id, target_agent_id, message)
    
    return {"status": "forwarded"}

@app.post("/iot/query")
async def query_iot_data(query_data: Dict[str, Any]):
    """Query IoT device data"""
    agent_id = query_data["agent_id"]
    device_type = query_data["device_type"]
    query_params = query_data["query_params"]
    
    # Transform query to MQTT format
    mqtt_query = data_transformer.transform_query_to_mqtt(query_params)
    
    # Query data from MQTT topics
    data = await mqtt_handler.query_device_data(device_type, mqtt_query)
    
    # Transform data to agent-friendly format
    transformed_data = data_transformer.transform_mqtt_to_agent(data)
    
    return {
        "status": "success",
        "data": transformed_data
    }

@app.post("/iot/control")
async def control_iot_device(control_data: Dict[str, Any]):
    """Send control command to IoT device"""
    agent_id = control_data["agent_id"]
    device_id = control_data["device_id"]
    command = control_data["command"]
    
    # Validate agent permissions
    if not await validate_agent_permissions(agent_id, device_id, "control"):
        raise HTTPException(status_code=403, detail="Agent not authorized")
    
    # Transform command to MQTT format
    mqtt_command = data_transformer.transform_command_to_mqtt(command)
    
    # Publish command to device
    await mqtt_handler.publish_command(device_id, mqtt_command)
    
    return {"status": "command_sent", "device_id": device_id}

@app.websocket("/ws/agents/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    
    # Subscribe to agent-specific events
    async def handle_iot_updates():
        async for update in mqtt_handler.subscribe_to_updates(agent_id):
            transformed_update = data_transformer.transform_mqtt_to_agent(update)
            await websocket.send_json(transformed_update)
    
    try:
        # Start handling IoT updates
        asyncio.create_task(handle_iot_updates())
        
        # Handle incoming messages from agent
        while True:
            data = await websocket.receive_json()
            await process_agent_websocket_message(agent_id, data)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Helper function for validating agent permissions
async def validate_agent_permissions(agent_id: str, device_id: str, action: str) -> bool:
    """Validate if an agent has permission to perform an action on a device"""
    # For POC, we'll allow all registered agents to control all devices
    # In production, implement proper ACL/RBAC here
    if agent_id in registered_agents:
        return True
    return False

async def process_agent_websocket_message(agent_id: str, data: Dict[str, Any]):
    # This is a placeholder for processing WebSocket messages from agents
    pass
