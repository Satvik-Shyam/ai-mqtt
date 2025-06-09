import asyncio
import json
import random
import time
from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt
from typing import Dict, Any

class BaseIoTDevice(ABC):
    def __init__(self, device_id: str, device_type: str, mqtt_broker: str, mqtt_port: int = 1883):
        self.device_id = device_id
        self.device_type = device_type
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = mqtt.Client(client_id=device_id)
        self.running = False
        
        # Setup MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Device {self.device_id} connected with result code {rc}")
        # Subscribe to device-specific command topic
        client.subscribe(f"devices/{self.device_id}/commands")
        
    def on_message(self, client, userdata, msg):
        """Handle incoming commands"""
        try:
            command = json.loads(msg.payload.decode())
            self.handle_command(command)
        except Exception as e:
            print(f"Error handling command: {e}")
    
    @abstractmethod
    def handle_command(self, command: Dict[str, Any]):
        """Handle device-specific commands"""
        pass
    
    @abstractmethod
    def generate_data(self) -> Dict[str, Any]:
        """Generate sensor data"""
        pass
    
    def publish_data(self, data: Dict[str, Any]):
        """Publish data to MQTT"""
        topic = f"devices/{self.device_type}/{self.device_id}/data"
        payload = json.dumps({
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": time.time(),
            "data": data
        })
        self.client.publish(topic, payload)
    
    async def run(self):
        """Main device loop"""
        self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.client.loop_start()
        self.running = True
        
        while self.running:
            data = self.generate_data()
            self.publish_data(data)
            await asyncio.sleep(5)  # Publish every 5 seconds
