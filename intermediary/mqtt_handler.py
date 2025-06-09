import asyncio
import json
import time
from typing import Dict, Any, List, AsyncGenerator
import paho.mqtt.client as mqtt
import os
from paho.mqtt.client import MQTTMessage

class MQTTHandler:
    """Handles MQTT communication for the intermediary"""
    
    def __init__(self):
        self.mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.client_id = f"intermediary-{int(time.time())}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        self.subscriptions = {}
        self.message_buffer = {}
        self.device_data_cache = {}
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        print(f"MQTT connected with result code {rc}")
        self.connected = True
        
        # Subscribe to all device data topics
        client.subscribe("devices/+/+/data")
        
        # Resubscribe to any topics that were previously subscribed to
        for topic in self.subscriptions:
            client.subscribe(topic)
    
    def on_message(self, client, userdata, msg: MQTTMessage):
        """Callback for when a message is received from the broker"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Store message in buffer for any active subscriptions
            for subscription_topic, callbacks in self.subscriptions.items():
                if self.topic_matches_subscription(subscription_topic, topic):
                    for callback in callbacks:
                        asyncio.create_task(callback(topic, payload))
            
            # If this is device data, cache it
            if topic.startswith("devices/") and topic.endswith("/data"):
                self.cache_device_data(topic, payload)
                
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        print(f"MQTT disconnected with result code {rc}")
        self.connected = False
    
    def topic_matches_subscription(self, subscription: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern with wildcards"""
        sub_parts = subscription.split('/')
        topic_parts = topic.split('/')
        
        if len(sub_parts) != len(topic_parts):
            return False
            
        for i, sub_part in enumerate(sub_parts):
            if sub_part != '+' and sub_part != '#' and sub_part != topic_parts[i]:
                return False
                
        return True
    
    def cache_device_data(self, topic: str, payload: Dict[str, Any]):
        """Cache device data for later retrieval"""
        # Extract device type and ID from topic
        # Format: devices/<device_type>/<device_id>/data
        parts = topic.split('/')
        if len(parts) == 4:
            device_type = parts[1]
            device_id = parts[2]
            
            if device_type not in self.device_data_cache:
                self.device_data_cache[device_type] = {}
                
            self.device_data_cache[device_type][device_id] = {
                "timestamp": time.time(),
                "data": payload
            }
    
    async def connect(self):
        """Connect to the MQTT broker"""
        if not self.connected:
            print(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            self.client.connect_async(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()
            
            # Wait for connection to establish
            for _ in range(10):  # Wait up to 10 seconds
                if self.connected:
                    break
                await asyncio.sleep(1)
                
            if not self.connected:
                print("Failed to connect to MQTT broker")
    
    async def disconnect(self):
        """Disconnect from the MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    async def subscribe(self, topic: str, callback=None):
        """Subscribe to a topic"""
        if not self.connected:
            await self.connect()
            
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
            self.client.subscribe(topic)
            
        if callback:
            self.subscriptions[topic].append(callback)
    
    async def unsubscribe(self, topic: str, callback=None):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            if callback:
                if callback in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(callback)
                    
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
                    self.client.unsubscribe(topic)
            else:
                del self.subscriptions[topic]
                self.client.unsubscribe(topic)
    
    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0):
        """Publish a message to a topic"""
        if not self.connected:
            await self.connect()
            
        message = json.dumps(payload)
        self.client.publish(topic, message, qos)
    
    async def publish_command(self, device_id: str, command: Dict[str, Any]):
        """Publish a command to a device"""
        topic = f"devices/{device_id}/commands"
        await self.publish(topic, command)
    
    async def query_device_data(self, device_type: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Query device data from cache based on parameters"""
        result = {"devices": {}}
        
        if device_type not in self.device_data_cache:
            return result
            
        # Apply filters from query_params
        time_range = query_params.get("time_range")
        location = query_params.get("location")
        max_age = None
        
        # Convert time_range to max_age in seconds
        if time_range == "last_minute":
            max_age = 60
        elif time_range == "last_5_minutes":
            max_age = 300
        elif time_range == "last_hour":
            max_age = 3600
        
        current_time = time.time()
        
        for device_id, device_data in self.device_data_cache[device_type].items():
            # Check if data is within time range
            if max_age and (current_time - device_data["timestamp"]) > max_age:
                continue
                
            # Check location filter if applicable
            if location and device_data["data"].get("data", {}).get("location") != location:
                continue
                
            # Add device data to result
            result["devices"][device_id] = device_data["data"].get("data", {})
            
        return result
    
    async def subscribe_to_updates(self, agent_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to real-time updates for an agent"""
        queue = asyncio.Queue()
        
        async def callback(topic, payload):
            await queue.put(payload)
        
        # Subscribe to all device data
        await self.subscribe("devices/+/+/data", callback)
        
        try:
            while True:
                update = await queue.get()
                yield update
                queue.task_done()
        finally:
            await self.unsubscribe("devices/+/+/data", callback)
