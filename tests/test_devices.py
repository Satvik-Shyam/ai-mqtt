import pytest
import asyncio
import json
from unittest.mock import Mock, MagicMock, patch
import paho.mqtt.client as mqtt
import sys
sys.path.append('.')

from iot_devices.base_device import BaseIoTDevice
from iot_devices.temperature_sensor import TemperatureSensor
from iot_devices.motion_detector import MotionDetector
from iot_devices.smart_switch import SmartSwitch


class TestBaseIoTDevice:
    """Test suite for BaseIoTDevice"""
    
    @pytest.fixture
    def mock_device(self):
        """Create a mock IoT device for testing"""
        class MockDevice(BaseIoTDevice):
            def handle_command(self, command):
                return {"handled": True}
            
            def generate_data(self):
                return {"test_data": 123}
        
        return MockDevice("test-device-1", "mock_device", "localhost")
    
    def test_device_initialization(self, mock_device):
        """Test device is initialized correctly"""
        assert mock_device.device_id == "test-device-1"
        assert mock_device.device_type == "mock_device"
        assert mock_device.mqtt_broker == "localhost"
        assert mock_device.mqtt_port == 1883
        assert isinstance(mock_device.client, mqtt.Client)
    
    @patch.object(mqtt.Client, 'connect')
    @patch.object(mqtt.Client, 'loop_start')
    @patch.object(mqtt.Client, 'publish')
    def test_publish_data(self, mock_publish, mock_loop, mock_connect, mock_device):
        """Test data publishing to MQTT"""
        test_data = {"temperature": 22.5, "humidity": 60}
        mock_device.publish_data(test_data)
        
        mock_publish.assert_called_once()
        topic, payload = mock_publish.call_args[0]
        
        assert topic == "devices/mock_device/test-device-1/data"
        
        payload_dict = json.loads(payload)
        assert payload_dict["device_id"] == "test-device-1"
        assert payload_dict["device_type"] == "mock_device"
        assert payload_dict["data"] == test_data
        assert "timestamp" in payload_dict
    
    def test_on_connect_subscribes_to_commands(self, mock_device):
        """Test device subscribes to command topic on connect"""
        mock_client = Mock()
        mock_device.on_connect(mock_client, None, None, 0)
        
        mock_client.subscribe.assert_called_once_with("devices/test-device-1/commands")
    
    def test_on_message_handles_valid_command(self, mock_device):
        """Test handling of valid command messages"""
        mock_client = Mock()
        mock_msg = Mock()
        mock_msg.payload = json.dumps({"action": "test_command"}).encode()
        
        with patch.object(mock_device, 'handle_command') as mock_handle:
            mock_device.on_message(mock_client, None, mock_msg)
            mock_handle.assert_called_once_with({"action": "test_command"})
    
    def test_on_message_handles_invalid_json(self, mock_device):
        """Test handling of invalid JSON in messages"""
        mock_client = Mock()
        mock_msg = Mock()
        mock_msg.payload = b"invalid json"
        
        # Should not raise exception
        mock_device.on_message(mock_client, None, mock_msg)


class TestTemperatureSensor:
    """Test suite for TemperatureSensor"""
    
    @pytest.fixture
    def temp_sensor(self):
        return TemperatureSensor("temp-sensor-1", "localhost")
    
    def test_temperature_sensor_initialization(self, temp_sensor):
        """Test temperature sensor specific initialization"""
        assert temp_sensor.device_type == "temperature_sensor"
        assert temp_sensor.base_temp == 20.0
        assert temp_sensor.variance == 5.0
    
    def test_generate_temperature_data(self, temp_sensor):
        """Test temperature data generation"""
        data = temp_sensor.generate_data()
        
        assert "temperature" in data
        assert "humidity" in data
        assert "unit" in data
        assert data["unit"] == "celsius"
        
        # Check temperature is within expected range
        assert 15.0 <= data["temperature"] <= 25.0
        assert 30.0 <= data["humidity"] <= 70.0
    
    def test_handle_calibrate_command(self, temp_sensor):
        """Test calibration command handling"""
        command = {
            "action": "calibrate",
            "base_temperature": 25.0
        }
        
        temp_sensor.handle_command(command)
        assert temp_sensor.base_temp == 25.0
    
    def test_multiple_data_generations_vary(self, temp_sensor):
        """Test that generated data varies over time"""
        readings = [temp_sensor.generate_data()["temperature"] for _ in range(10)]
        
        # Check that not all readings are identical
        assert len(set(readings)) > 1


class TestMotionDetector:
    """Test suite for MotionDetector"""
    
    @pytest.fixture
    def motion_detector(self):
        return MotionDetector("motion-1", "localhost")
    
    def test_motion_detector_initialization(self, motion_detector):
        """Test motion detector specific initialization"""
        assert motion_detector.device_type == "motion_detector"
        assert motion_detector.sensitivity == 0.7
        assert motion_detector.location == "unknown"
    
    def test_generate_motion_data(self, motion_detector):
        """Test motion detection data generation"""
        motion_detector.location = "living_room"
        
        # Generate multiple readings to ensure we get both states
        readings = [motion_detector.generate_data() for _ in range(20)]
        
        # Check data structure
        for data in readings:
            assert "motion_detected" in data
            assert "location" in data
            assert "sensitivity" in data
            assert isinstance(data["motion_detected"], bool)
            assert data["location"] == "living_room"
            assert data["sensitivity"] == 0.7
        
        # Verify we get both true and false readings
        motion_values = [r["motion_detected"] for r in readings]
        assert True in motion_values
        assert False in motion_values
    
    def test_handle_set_location_command(self, motion_detector):
        """Test setting location via command"""
        command = {
            "action": "set_location",
            "location": "bedroom"
        }
        
        motion_detector.handle_command(command)
        assert motion_detector.location == "bedroom"
    
    def test_handle_set_sensitivity_command(self, motion_detector):
        """Test setting sensitivity via command"""
        command = {
            "action": "set_sensitivity",
            "sensitivity": 0.9
        }
        
        motion_detector.handle_command(command)
        assert motion_detector.sensitivity == 0.9


class TestSmartSwitch:
    """Test suite for SmartSwitch"""
    
    @pytest.fixture
    def smart_switch(self):
        return SmartSwitch("switch-1", "localhost")
    
    def test_smart_switch_initialization(self, smart_switch):
        """Test smart switch specific initialization"""
        assert smart_switch.device_type == "smart_switch"
        assert smart_switch.state == "off"
        assert smart_switch.brightness == 0
        assert smart_switch.mode == "normal"
    
    def test_generate_switch_data(self, smart_switch):
        """Test switch status data generation"""
        # Test with switch off
        data_off = smart_switch.generate_data()
        assert data_off["state"] == "off"
        assert data_off["brightness"] == 0
        assert data_off["mode"] == "normal"
        assert data_off["power_consumption"] == 0
        
        # Turn on and test
        smart_switch.state = "on"
        smart_switch.brightness = 75
        data_on = smart_switch.generate_data()
        assert data_on["state"] == "on"
        assert data_on["brightness"] == 75
        assert data_on["power_consumption"] > 0
    
    def test_handle_turn_on_command(self, smart_switch):
        """Test turning switch on via command"""
        command = {
            "action": "turn_on",
            "brightness": 80
        }
        
        smart_switch.handle_command(command)
        assert smart_switch.state == "on"
        assert smart_switch.brightness == 80
    
    def test_handle_turn_off_command(self, smart_switch):
        """Test turning switch off via command"""
        smart_switch.state = "on"
        smart_switch.brightness = 100
        
        command = {"action": "turn_off"}
        
        smart_switch.handle_command(command)
        assert smart_switch.state == "off"
        assert smart_switch.brightness == 0
    
    def test_handle_set_brightness_command(self, smart_switch):
        """Test setting brightness via command"""
        smart_switch.state = "on"
        
        command = {
            "action": "set_brightness",
            "brightness": 50
        }
        
        smart_switch.handle_command(command)
        assert smart_switch.brightness == 50
    
    def test_handle_set_mode_command(self, smart_switch):
        """Test setting mode via command"""
        command = {
            "action": "set_mode",
            "mode": "eco"
        }
        
        smart_switch.handle_command(command)
        assert smart_switch.mode == "eco"
    
    def test_power_consumption_calculation(self, smart_switch):
        """Test power consumption varies with brightness"""
        smart_switch.state = "on"
        
        # Test different brightness levels
        smart_switch.brightness = 0
        power_0 = smart_switch.generate_data()["power_consumption"]
        
        smart_switch.brightness = 50
        power_50 = smart_switch.generate_data()["power_consumption"]
        
        smart_switch.brightness = 100
        power_100 = smart_switch.generate_data()["power_consumption"]
        
        # Power should increase with brightness
        assert power_0 < power_50 < power_100

