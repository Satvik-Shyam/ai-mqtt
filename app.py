# app.py
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import uvicorn
from iot_devices.smart_switch import SmartSwitch
from iot_devices.motion_detector import MotionDetector
from ai_agents.control_agent import ControlAgent
from ai_agents.monitoring_agent import MonitoringAgent
from ai_agents.analytics_agent import AnalyticsAgent

app = FastAPI()

# Setup devices and agents
mqtt_broker = "localhost"
devices = {
    "switch-1": SmartSwitch("switch-1", mqtt_broker),
    "motion-1": MotionDetector("motion-1", mqtt_broker)
}

agents = {
    "control-1": ControlAgent("control-1", "http://localhost:8000"),
    "monitor-1": MonitoringAgent("monitor-1", "http://localhost:8000"),
    "analytics-1": AnalyticsAgent("analytics-1", "http://localhost:8000")
}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("static/index.html") as f:
        return f.read()

@app.get("/api/devices")
async def get_devices():
    result = {}
    for device_id, device in devices.items():
        result[device_id] = device.generate_data()
    return result

@app.post("/api/devices/{device_id}/command")
async def send_command(device_id: str, command: dict):
    if device_id in devices:
        devices[device_id].handle_command(command)
        return {"status": "success", "device_id": device_id}
    return {"status": "error", "message": f"Device {device_id} not found"}

@app.get("/api/analytics/energy")
async def get_energy_analysis():
    return await agents["analytics-1"].analyze_energy_consumption()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send device updates every 2 seconds
            device_data = {}
            for device_id, device in devices.items():
                device_data[device_id] = device.generate_data()
            
            await websocket.send_json(device_data)
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)