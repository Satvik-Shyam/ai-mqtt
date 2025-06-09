"""
MQTT Configuration Module

This module provides configuration settings for MQTT connections.
"""

import os
from typing import Dict, Any

# Default MQTT configuration
DEFAULT_CONFIG = {
    "broker": "localhost",
    "port": 1883,
    "websocket_port": 9001,
    "keepalive": 60,
    "qos": 1,
    "retain": False,
    "clean_session": True,
    "reconnect_on_failure": True,
    "reconnect_delay": 5,  # seconds
    "max_reconnect_attempts": 12,
    "username": None,
    "password": None,
    "tls_enabled": False,
    "tls_ca_certs": None,
    "tls_certfile": None,
    "tls_keyfile": None,
    "tls_insecure": False
}

def get_mqtt_config() -> Dict[str, Any]:
    """
    Get MQTT configuration from environment variables or defaults.
    
    Returns:
        Dict[str, Any]: MQTT configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if available
    if os.getenv("MQTT_BROKER"):
        config["broker"] = os.getenv("MQTT_BROKER")
        
    if os.getenv("MQTT_PORT"):
        config["port"] = int(os.getenv("MQTT_PORT"))
        
    if os.getenv("MQTT_WEBSOCKET_PORT"):
        config["websocket_port"] = int(os.getenv("MQTT_WEBSOCKET_PORT"))
        
    if os.getenv("MQTT_USERNAME"):
        config["username"] = os.getenv("MQTT_USERNAME")
        
    if os.getenv("MQTT_PASSWORD"):
        config["password"] = os.getenv("MQTT_PASSWORD")
        
    if os.getenv("MQTT_TLS_ENABLED") and os.getenv("MQTT_TLS_ENABLED").lower() in ("true", "1", "yes"):
        config["tls_enabled"] = True
        
    if os.getenv("MQTT_TLS_CA_CERTS"):
        config["tls_ca_certs"] = os.getenv("MQTT_TLS_CA_CERTS")
        
    if os.getenv("MQTT_TLS_CERTFILE"):
        config["tls_certfile"] = os.getenv("MQTT_TLS_CERTFILE")
        
    if os.getenv("MQTT_TLS_KEYFILE"):
        config["tls_keyfile"] = os.getenv("MQTT_TLS_KEYFILE")
        
    return config

def get_topic_structure() -> Dict[str, str]:
    """
    Get the topic structure for the MQTT messaging.
    
    Returns:
        Dict[str, str]: Topic structure dictionary
    """
    return {
        "device_data": "devices/{device_type}/{device_id}/data",
        "device_command": "devices/{device_id}/commands",
        "agent_message": "agents/{agent_id}/messages",
        "agent_command": "agents/{agent_id}/commands",
        "system_status": "system/status",
        "system_control": "system/control"
    }

def get_qos_level(topic_type: str) -> int:
    """
    Get the appropriate QoS level for a given topic type.
    
    Args:
        topic_type (str): Type of topic
        
    Returns:
        int: QoS level (0, 1, or 2)
    """
    qos_levels = {
        "device_data": 0,  # At most once delivery
        "device_command": 1,  # At least once delivery
        "agent_message": 1,  # At least once delivery
        "agent_command": 2,  # Exactly once delivery
        "system_status": 1,  # At least once delivery
        "system_control": 2,  # Exactly once delivery
    }
    
    return qos_levels.get(topic_type, 1)  # Default to QoS 1
