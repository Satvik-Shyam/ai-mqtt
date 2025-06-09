import random
import time
from typing import Dict, Any
from .base_device import BaseIoTDevice

class MotionDetector(BaseIoTDevice):
    def __init__(self, device_id: str, mqtt_broker: str):
        super().__init__(device_id, "motion_detector", mqtt_broker)
        self.location = "unknown"  # Default location (for test compatibility)
        self.sensitivity = 0.7  # Default sensitivity (0-1)
        self.last_motion = 0  # Timestamp of last detected motion
        
    def generate_data(self) -> Dict[str, Any]:
        # Simulate motion detection with random probability
        # Higher probability during certain times of day
        current_hour = time.localtime().tm_hour
        
        # Higher probability during morning and evening
        time_factor = 1.5 if (7 <= current_hour <= 9) or (17 <= current_hour <= 22) else 1.0
        
        # Calculate motion probability
        motion_probability = 0.3 * time_factor * self.sensitivity
        motion_detected = random.random() < motion_probability
        
        if motion_detected:
            self.last_motion = time.time()
        
        # Calculate time since last motion
        time_since_motion = time.time() - self.last_motion if self.last_motion > 0 else float('inf')
        
        return {
            "motion_detected": motion_detected,
            "location": self.location,
            "sensitivity": self.sensitivity,  # Include sensitivity for test compatibility
            "time_since_motion": round(time_since_motion, 2) if time_since_motion < float('inf') else None
        }
    
    def handle_command(self, command: Dict[str, Any]):
        if command.get("action") == "set_sensitivity":
            new_sensitivity = command.get("sensitivity")
            if new_sensitivity is not None and 0 <= new_sensitivity <= 1:
                self.sensitivity = new_sensitivity
                print(f"Motion detector {self.device_id} sensitivity set to {self.sensitivity}")
                
        elif command.get("action") == "set_location":
            new_location = command.get("location")
            if new_location:
                self.location = new_location
                print(f"Motion detector {self.device_id} location set to {self.location}")
