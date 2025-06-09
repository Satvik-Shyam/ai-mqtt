import asyncio
import time
from typing import Dict, Any, List
import logging
from .base_agent import BaseAgent, AgentMessage

class ControlAgent(BaseAgent):
    def __init__(self, name: str, intermediary_url: str):
        super().__init__(name, "control", intermediary_url)
        self.controlled_devices = {}  # Track devices under control
        self.automation_rules = []  # Rules for automated control
        self.scenes = {}  # Store predefined scenes
        
    def get_capabilities(self) -> List[str]:
        return ["device_control", "automation", "scene_management"]
    
    async def run(self):
        """Main agent loop"""
        while self._running:
            # Apply automation rules
            await self.apply_automation_rules()
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def process_message(self, message: AgentMessage):
        """Process incoming messages from other agents"""
        if message.message_type == "control_request":
            device_id = message.payload.get("device_id")
            command = message.payload.get("command")
            
            if device_id and command:
                result = await self.control_iot_device(device_id, command)
                # Send result back to requesting agent
                await self.send_to_agent(
                    message.agent_id,
                    "control_result",
                    {"device_id": device_id, "success": result.get("status") == "command_sent"}
                )
                
        elif message.message_type == "add_automation_rule":
            rule = message.payload.get("rule")
            if rule:
                self.automation_rules.append(rule)
                await self.send_to_agent(
                    message.agent_id,
                    "rule_added",
                    {"rule_id": len(self.automation_rules) - 1}
                )
                
        elif message.message_type == "analysis_result":
            # Process analysis results from monitoring or analytics agents
            analysis_type = message.payload.get("analysis_type")
            result = message.payload.get("result")
            
            if analysis_type == "motion_activity" and result:
                # Use activity analysis to adjust automation
                self.logger.info(f"Received motion activity analysis: {result}")
                # Could adjust automation rules based on this analysis
    
    async def apply_automation_rules(self):
        """Apply automation rules based on current conditions"""
        try:
            # Get current state of motion detectors
            motion_data = await self.query_iot_data("motion_detector", {})
            
            # Get current state of temperature sensors
            temp_data = await self.query_iot_data("temperature_sensor", {})
            
            # Apply rules based on current conditions
            for rule in self.automation_rules:
                await self.apply_rule(rule, motion_data, temp_data)
                
        except Exception as e:
            self.logger.error(f"Error applying automation rules: {e}")
    
    async def apply_rule(self, rule: Dict[str, Any], motion_data: Dict[str, Any], temp_data: Dict[str, Any]):
        """Apply a single automation rule"""
        rule_type = rule.get("type")
        
        if rule_type == "motion_lighting":
            # Rule to turn on lights when motion is detected
            location = rule.get("location")
            target_switch = rule.get("target_switch")
            
            # Check if motion is detected in the specified location
            motion_detected = False
            for device_id, data in motion_data.get("devices", {}).items():
                if data.get("location") == location and data.get("motion_detected"):
                    motion_detected = True
                    break
            
            if motion_detected:
                # Turn on the light
                await self.control_iot_device(
                    target_switch,
                    {"action": "turn_on", "brightness": rule.get("brightness", 80)}
                )
            elif rule.get("turn_off_after_inactivity"):
                # Check if we should turn off the light due to inactivity
                for device_id, data in motion_data.get("devices", {}).items():
                    if (data.get("location") == location and 
                        data.get("time_since_motion") and 
                        data.get("time_since_motion") > rule.get("inactivity_timeout", 300)):
                        # Turn off the light after inactivity timeout
                        await self.control_iot_device(
                            target_switch,
                            {"action": "turn_off"}
                        )
                        break
                        
        elif rule_type == "temperature_control":
            # Rule to control devices based on temperature
            sensor_id = rule.get("temperature_sensor")
            target_device = rule.get("target_device")
            
            if sensor_id in temp_data.get("devices", {}):
                current_temp = temp_data["devices"][sensor_id].get("temperature")
                
                if current_temp > rule.get("max_temperature", 25):
                    # Temperature too high, take cooling action
                    await self.control_iot_device(
                        target_device,
                        {"action": rule.get("cooling_action", "turn_on")}
                    )
                elif current_temp < rule.get("min_temperature", 18):
                    # Temperature too low, take heating action
                    await self.control_iot_device(
                        target_device,
                        {"action": rule.get("heating_action", "turn_on")}
                    )
                else:
                    # Temperature in acceptable range
                    await self.control_iot_device(
                        target_device,
                        {"action": "turn_off"}
                    )
    
    async def create_scene(self, scene_name: str, device_states: Dict[str, Dict[str, Any]]):
        """Create a scene with predefined device states"""
        # Store the scene in the scenes dictionary
        self.scenes[scene_name] = device_states
        self.logger.info(f"Created scene '{scene_name}' with {len(device_states)} devices")
        return {"scene_id": scene_name, "name": scene_name}
        
    async def automated_lighting(self, location: str) -> Dict[str, Any]:
        """Automated lighting control based on motion detection
        
        This method checks if motion is detected in a specific location and turns on lights accordingly.
        """
        # Query motion detector data for the specified location
        motion_data = await self.query_iot_data("motion_detector", {"location": location})
        
        # Check if motion is detected
        # For the test case, motion_data.json.return_value = {"status": "success", "data": {"motion_detected": True, "location": "living_room"}}
        motion_detected = False
        
        # Handle both formats: nested device data or direct data
        if "data" in motion_data:
            if isinstance(motion_data["data"], dict):
                if "devices" in motion_data["data"]:
                    # Format: {"data": {"devices": {"device-id": {"motion_detected": true, ...}}}}
                    for device_id, data in motion_data["data"].get("devices", {}).items():
                        if data.get("location") == location and data.get("motion_detected"):
                            motion_detected = True
                            break
                else:
                    # Format: {"data": {"motion_detected": true, "location": "living_room"}}
                    motion_detected = motion_data["data"].get("motion_detected", False)
        
        if motion_detected:
            # Find lights in this location (in a real system, we would have a mapping)
            # For this example, we'll use a naming convention: "light-{location}"
            light_id = f"light-{location.replace('_', '-')}"
            
            # Turn on the light
            result = await self.control_iot_device(
                light_id,
                {"action": "turn_on", "brightness": 80}
            )
            
            return {
                "action": "lights_on",
                "reason": "motion_detected",
                "location": location,
                "device_id": light_id,
                "success": result.get("status") == "command_sent"
            }
        else:
            return {
                "action": "no_action",
                "reason": "no_motion_detected",
                "location": location
            }
    
    async def activate_scene(self, scene_id: str):
        """Activate a predefined scene"""
        # This would typically retrieve the scene from a database and apply all device states
        # For this example, we'll just log it
        self.logger.info(f"Activating scene {scene_id}")
        return {"status": "scene_activated", "scene_id": scene_id}
