import random
from typing import Dict, Any
from .base_device import BaseIoTDevice

class TemperatureSensor(BaseIoTDevice):
    def __init__(self, device_id: str, mqtt_broker: str):
        super().__init__(device_id, "temperature_sensor", mqtt_broker)
        self.base_temp = 20.0
        self.variance = 5.0
        
    def generate_data(self) -> Dict[str, Any]:
        temperature = self.base_temp + random.uniform(-self.variance, self.variance)
        humidity = 50 + random.uniform(-20, 20)
        
        return {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "unit": "celsius"
        }
    
    def handle_command(self, command: Dict[str, Any]):
        if command.get("action") == "calibrate":
            self.base_temp = command.get("base_temperature", self.base_temp)
            print(f"Temperature sensor {self.device_id} calibrated to {self.base_temp}°C")
