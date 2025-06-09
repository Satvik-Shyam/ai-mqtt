"""
Data Transformer for the AI-IoT Intermediary

This module handles transformations between different data formats:
- MQTT message format to agent-friendly format
- Agent queries to MQTT queries
- Agent commands to device commands
"""

import time
from typing import Dict, Any, List

class DataTransformer:
    """Transforms data between different formats in the system"""
    
    def transform_mqtt_to_agent(self, mqtt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MQTT data format to agent-friendly format"""
        # If this is already in the right format (e.g., from query_device_data)
        if "devices" in mqtt_data:
            return mqtt_data
            
        # If this is a single MQTT message
        if "device_id" in mqtt_data and "device_type" in mqtt_data and "data" in mqtt_data:
            device_id = mqtt_data["device_id"]
            return {
                "devices": {
                    device_id: mqtt_data["data"]
                },
                "timestamp": mqtt_data.get("timestamp", time.time())
            }
            
        # Default case - just return as is
        return mqtt_data
    
    def transform_query_to_mqtt(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agent query parameters to MQTT query format"""
        mqtt_query = {}
        
        # Map time-based parameters
        if "time_range" in query_params:
            mqtt_query["time_range"] = query_params["time_range"]
            
        # Map location parameters
        if "location" in query_params:
            mqtt_query["location"] = query_params["location"]
            
        # Map device-specific parameters
        if "device_id" in query_params:
            mqtt_query["device_id"] = query_params["device_id"]
            
        # Map any other parameters directly
        for key, value in query_params.items():
            if key not in mqtt_query:
                mqtt_query[key] = value
                
        return mqtt_query
    
    def transform_command_to_mqtt(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agent command to MQTT device command format"""
        mqtt_command = {
            "timestamp": time.time()
        }
        
        # Map action and parameters
        if "action" in command:
            mqtt_command["action"] = command["action"]
            
        # Copy all other parameters
        for key, value in command.items():
            if key != "action" and key not in mqtt_command:
                mqtt_command[key] = value
                
        return mqtt_command
    
    def transform_agent_message_to_mqtt(self, agent_message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agent-to-agent message to MQTT format for publishing"""
        return {
            "source_agent_id": agent_message.get("source_agent_id"),
            "target_agent_id": agent_message.get("target_agent_id"),
            "message_type": agent_message.get("message_type"),
            "payload": agent_message.get("payload", {}),
            "timestamp": agent_message.get("timestamp", time.time()),
            "correlation_id": agent_message.get("correlation_id")
        }
    
    def transform_mqtt_to_agent_message(self, mqtt_message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MQTT format back to agent-to-agent message format"""
        return {
            "source_agent_id": mqtt_message.get("source_agent_id"),
            "target_agent_id": mqtt_message.get("target_agent_id"),
            "message_type": mqtt_message.get("message_type"),
            "payload": mqtt_message.get("payload", {}),
            "timestamp": mqtt_message.get("timestamp", time.time()),
            "correlation_id": mqtt_message.get("correlation_id")
        }
    
    def transform_device_data_for_storage(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform device data for efficient storage"""
        # Extract the essential information
        return {
            "device_id": device_data.get("device_id"),
            "device_type": device_data.get("device_type"),
            "timestamp": device_data.get("timestamp", time.time()),
            "data": device_data.get("data", {})
        }
    
    def transform_stored_data_for_query(self, stored_data: List[Dict[str, Any]], 
                                      query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform stored data based on query parameters"""
        result = {"devices": {}}
        
        # Apply filters from query parameters
        time_range = query_params.get("time_range")
        location = query_params.get("location")
        device_id = query_params.get("device_id")
        
        # Determine time filter
        max_age = None
        if time_range == "last_minute":
            max_age = 60
        elif time_range == "last_5_minutes":
            max_age = 300
        elif time_range == "last_hour":
            max_age = 3600
        elif time_range == "last_day":
            max_age = 86400
            
        current_time = time.time()
        
        for data_point in stored_data:
            # Apply time filter
            if max_age and (current_time - data_point.get("timestamp", 0)) > max_age:
                continue
                
            # Apply device ID filter
            if device_id and data_point.get("device_id") != device_id:
                continue
                
            # Apply location filter
            if location and data_point.get("data", {}).get("location") != location:
                continue
                
            # Add to result
            device_id = data_point.get("device_id")
            if device_id not in result["devices"]:
                result["devices"][device_id] = data_point.get("data", {})
                
        return result
