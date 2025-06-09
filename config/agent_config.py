"""
Agent Configuration Module

This module provides configuration settings for AI agents.
"""

import os
from typing import Dict, Any, List

# Default agent configuration
DEFAULT_AGENT_CONFIG = {
    "monitoring_agent": {
        "check_interval": 30,  # seconds
        "alert_thresholds": {
            "temperature_sensor": {
                "high_temp": 30.0,
                "low_temp": 10.0
            },
            "motion_detector": {
                "inactivity_period": 3600  # 1 hour in seconds
            },
            "smart_switch": {
                "max_power": 10.0  # watts
            }
        },
        "data_retention": {
            "max_data_points": 1000,
            "max_age": 86400  # 1 day in seconds
        }
    },
    "control_agent": {
        "check_interval": 10,  # seconds
        "default_rules": [
            {
                "type": "motion_lighting",
                "location": "room_1",
                "target_switch": "switch-0",
                "brightness": 80,
                "turn_off_after_inactivity": True,
                "inactivity_timeout": 300  # 5 minutes
            }
        ]
    },
    "analytics_agent": {
        "analysis_interval": 60,  # seconds
        "data_collection_interval": 60,  # seconds
        "prediction_models": {
            "energy_consumption": "simple_average",  # or "ml_model"
            "occupancy_pattern": "time_based"  # or "ml_model"
        }
    }
}

def get_agent_config(agent_type: str = None) -> Dict[str, Any]:
    """
    Get agent configuration from environment variables or defaults.
    
    Args:
        agent_type (str, optional): Type of agent to get config for. If None, returns all configs.
        
    Returns:
        Dict[str, Any]: Agent configuration dictionary
    """
    config = DEFAULT_AGENT_CONFIG.copy()
    
    # Override with environment variables if available
    if os.getenv("MONITORING_CHECK_INTERVAL"):
        config["monitoring_agent"]["check_interval"] = int(os.getenv("MONITORING_CHECK_INTERVAL"))
        
    if os.getenv("CONTROL_CHECK_INTERVAL"):
        config["control_agent"]["check_interval"] = int(os.getenv("CONTROL_CHECK_INTERVAL"))
        
    if os.getenv("ANALYTICS_INTERVAL"):
        config["analytics_agent"]["analysis_interval"] = int(os.getenv("ANALYTICS_INTERVAL"))
        
    # Return specific agent config if requested
    if agent_type:
        return config.get(f"{agent_type}_agent", {})
        
    return config

def get_agent_capabilities(agent_type: str) -> List[str]:
    """
    Get the capabilities for a specific agent type.
    
    Args:
        agent_type (str): Type of agent
        
    Returns:
        List[str]: List of capabilities
    """
    capabilities = {
        "monitoring": ["device_monitoring", "anomaly_detection", "trend_analysis"],
        "control": ["device_control", "automation", "scene_management"],
        "analytics": ["data_analytics", "pattern_recognition", "predictive_analysis"]
    }
    
    return capabilities.get(agent_type, [])

def get_agent_permissions(agent_type: str) -> Dict[str, List[str]]:
    """
    Get the permissions for a specific agent type.
    
    Args:
        agent_type (str): Type of agent
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping resource types to allowed actions
    """
    permissions = {
        "monitoring": {
            "device": ["read"],
            "agent": ["read"]
        },
        "control": {
            "device": ["read", "control"],
            "agent": ["read"]
        },
        "analytics": {
            "device": ["read"],
            "agent": ["read"]
        }
    }
    
    return permissions.get(agent_type, {})
