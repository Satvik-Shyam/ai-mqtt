"""
IoT Device Simulator

This module simulates multiple IoT devices sending data to the MQTT broker.
"""

import asyncio
import sys
import os
import random
import argparse
from typing import List

from .temperature_sensor import TemperatureSensor
from .motion_detector import MotionDetector
from .smart_switch import SmartSwitch

async def run_simulator(num_temp_sensors: int = 3, 
                       num_motion_detectors: int = 2,
                       num_smart_switches: int = 2,
                       mqtt_broker: str = None):
    """
    Run the IoT device simulator with the specified number of devices.
    
    Args:
        num_temp_sensors (int): Number of temperature sensors to simulate
        num_motion_detectors (int): Number of motion detectors to simulate
        num_smart_switches (int): Number of smart switches to simulate
        mqtt_broker (str): MQTT broker address
    """
    # Get MQTT broker from environment if not specified
    if not mqtt_broker:
        mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        
    print(f"Starting IoT device simulator with MQTT broker: {mqtt_broker}")
    print(f"Simulating {num_temp_sensors} temperature sensors, "
          f"{num_motion_detectors} motion detectors, and "
          f"{num_smart_switches} smart switches")
    
    # Create devices
    devices = []
    
    # Temperature sensors
    for i in range(num_temp_sensors):
        device_id = f"temp-sensor-{i}"
        device = TemperatureSensor(device_id, mqtt_broker)
        devices.append(device)
        print(f"Created temperature sensor: {device_id}")
        
    # Motion detectors
    for i in range(num_motion_detectors):
        device_id = f"motion-{i}"
        device = MotionDetector(device_id, mqtt_broker)
        # Assign different locations to motion detectors
        if i % 2 == 0:
            device.location = "room_1"
        else:
            device.location = "room_2"
        devices.append(device)
        print(f"Created motion detector: {device_id} in {device.location}")
        
    # Smart switches
    for i in range(num_smart_switches):
        device_id = f"switch-{i}"
        device = SmartSwitch(device_id, mqtt_broker)
        # Assign different locations to switches
        if i % 2 == 0:
            device.location = "room_1"
        else:
            device.location = "room_2"
        devices.append(device)
        print(f"Created smart switch: {device_id} in {device.location}")
    
    # Start all devices
    device_tasks = []
    for device in devices:
        device_tasks.append(asyncio.create_task(device.run()))
        
    print(f"All {len(devices)} devices started")
    
    try:
        # Run forever
        while True:
            await asyncio.sleep(60)
            print(f"Devices running... ({len(devices)} active)")
    except KeyboardInterrupt:
        print("Stopping simulator...")
    finally:
        # Stop all devices
        for device in devices:
            device.running = False
            
        # Cancel all tasks
        for task in device_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*device_tasks, return_exceptions=True)
        print("Simulator stopped")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="IoT Device Simulator")
    parser.add_argument("--temp-sensors", type=int, default=3,
                        help="Number of temperature sensors to simulate")
    parser.add_argument("--motion-detectors", type=int, default=2,
                        help="Number of motion detectors to simulate")
    parser.add_argument("--smart-switches", type=int, default=2,
                        help="Number of smart switches to simulate")
    parser.add_argument("--mqtt-broker", type=str, default=None,
                        help="MQTT broker address (default: from environment or localhost)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_simulator(
        num_temp_sensors=args.temp_sensors,
        num_motion_detectors=args.motion_detectors,
        num_smart_switches=args.smart_switches,
        mqtt_broker=args.mqtt_broker
    ))
