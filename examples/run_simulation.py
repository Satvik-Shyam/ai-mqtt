import asyncio
import sys
sys.path.append('.')

from ai_agents.monitoring_agent import MonitoringAgent
from ai_agents.control_agent import ControlAgent
from ai_agents.analytics_agent import AnalyticsAgent
from iot_devices.temperature_sensor import TemperatureSensor
from iot_devices.motion_detector import MotionDetector
from iot_devices.smart_switch import SmartSwitch

async def main():
    # Configuration
    INTERMEDIARY_URL = "http://localhost:8000"
    MQTT_BROKER = "localhost"
    
    # Create AI Agents
    monitoring_agent = MonitoringAgent("Monitor-1", INTERMEDIARY_URL)
    control_agent = ControlAgent("Control-1", INTERMEDIARY_URL)
    analytics_agent = AnalyticsAgent("Analytics-1", INTERMEDIARY_URL)
    
    # Create IoT Devices
    temp_sensors = [
        TemperatureSensor(f"temp-sensor-{i}", MQTT_BROKER) 
        for i in range(3)
    ]
    motion_detectors = [
        MotionDetector(f"motion-{i}", MQTT_BROKER) 
        for i in range(2)
    ]
    smart_switches = [
        SmartSwitch(f"switch-{i}", MQTT_BROKER) 
        for i in range(2)
    ]
    
    # Start all components
    print("Starting AI Agents...")
    await monitoring_agent.start()
    await control_agent.start()
    await analytics_agent.start()
    
    print("Starting IoT Devices...")
    device_tasks = []
    for device in temp_sensors + motion_detectors + smart_switches:
        device_tasks.append(asyncio.create_task(device.run()))
    
    # Simulation scenarios
    await asyncio.sleep(5)  # Let everything initialize
    
    print("\n=== Scenario 1: Monitoring Agent queries temperature data ===")
    temp_data = await monitoring_agent.query_iot_data(
        "temperature_sensor", 
        {"time_range": "last_5_minutes"}
    )
    print(f"Temperature data: {temp_data}")
    
    print("\n=== Scenario 2: Analytics Agent requests analysis from Monitoring Agent ===")
    await analytics_agent.send_to_agent(
        monitoring_agent.agent_id,
        "request_analysis",
        {"analysis_type": "temperature_trend"}
    )
    
    print("\n=== Scenario 3: Control Agent adjusts smart switch based on motion ===")
    motion_data = await control_agent.query_iot_data(
        "motion_detector",
        {"location": "room_1"}
    )
    
    if motion_data.get("motion_detected"):
        await control_agent.control_iot_device(
            "switch-0",
            {"action": "turn_on", "brightness": 80}
        )
    
    # Run for a while to see interactions
    await asyncio.sleep(60)
    
    # Cleanup
    print("\nStopping simulation...")
    await monitoring_agent.stop()
    await control_agent.stop()
    await analytics_agent.stop()
    
    for task in device_tasks:
        task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
