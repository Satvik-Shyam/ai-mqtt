import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
sys.path.append('.')

from ai_agents.base_agent import BaseAgent, AgentMessage
from ai_agents.monitoring_agent import MonitoringAgent
from ai_agents.control_agent import ControlAgent
from ai_agents.analytics_agent import AnalyticsAgent


class TestBaseAgent:
    """Test suite for BaseAgent functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        class MockAgent(BaseAgent):
            def get_capabilities(self):
                return ["test_capability"]
            
            async def process_message(self, message: AgentMessage):
                return {"processed": True}
        
        return MockAgent("test-agent", "mock", "http://localhost:8000")

    def test_agent_creation(self, mock_agent):
        """Test that a mock agent can be created."""
        assert mock_agent.name == "test-agent"
        assert mock_agent.agent_type == "mock"
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_agent):
        """Test agent is initialized with correct attributes"""
        assert mock_agent.name == "test-agent"
        assert mock_agent.agent_type == "mock"
        assert mock_agent.intermediary_url == "http://localhost:8000"
        assert mock_agent.agent_id is not None
        assert len(mock_agent.agent_id) == 36  # UUID length
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_agent_registration(self, mock_post, mock_agent):
        """Test agent registers with intermediary"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        await mock_agent.register_with_intermediary()
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/agents/register"
        
        # Check registration payload
        registration_data = call_args[1]["json"]
        assert registration_data["agent_id"] == mock_agent.agent_id
        assert registration_data["name"] == "test-agent"
        assert registration_data["agent_type"] == "mock"
        assert registration_data["capabilities"] == ["test_capability"]
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_send_to_agent(self, mock_post, mock_agent):
        """Test agent-to-agent communication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        target_agent_id = "target-agent-123"
        message_type = "test_message"
        payload = {"data": "test_data"}
        
        await mock_agent.send_to_agent(target_agent_id, message_type, payload)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/agents/message"
        
        # Check message structure
        message_data = call_args[1]["json"]
        assert message_data["source_agent_id"] == mock_agent.agent_id
        assert message_data["target_agent_id"] == target_agent_id
        assert message_data["message"]["message_type"] == message_type
        assert message_data["message"]["payload"] == payload
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_query_iot_data(self, mock_post, mock_agent):
        """Test querying IoT data through intermediary"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"temperature": 22.5}
        }
        mock_post.return_value = mock_response
        
        result = await mock_agent.query_iot_data(
            "temperature_sensor",
            {"time_range": "last_hour"}
        )
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/iot/query"
        
        query_data = call_args[1]["json"]
        assert query_data["agent_id"] == mock_agent.agent_id
        assert query_data["device_type"] == "temperature_sensor"
        assert query_data["query_params"]["time_range"] == "last_hour"
        
        assert result["data"]["temperature"] == 22.5
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_control_iot_device(self, mock_post, mock_agent):
        """Test sending control commands to IoT devices"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "command_sent",
            "device_id": "switch-1"
        }
        mock_post.return_value = mock_response
        
        result = await mock_agent.control_iot_device(
            "switch-1",
            {"action": "turn_on", "brightness": 75}
        )
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/iot/control"
        
        control_data = call_args[1]["json"]
        assert control_data["agent_id"] == mock_agent.agent_id
        assert control_data["device_id"] == "switch-1"
        assert control_data["command"]["action"] == "turn_on"
        assert control_data["command"]["brightness"] == 75
        
        assert result["status"] == "command_sent"


class TestMonitoringAgent:
    """Test suite for MonitoringAgent"""
    
    @pytest.fixture
    def monitoring_agent(self):
        return MonitoringAgent("monitor-1", "http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_monitoring_agent_capabilities(self, monitoring_agent):
        """Test monitoring agent has correct capabilities"""
        capabilities = monitoring_agent.get_capabilities()
        assert "temperature_monitoring" in capabilities
        assert "motion_detection" in capabilities
        assert "anomaly_detection" in capabilities
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_analyze_temperature_trends(self, mock_post, monitoring_agent):
        """Test temperature trend analysis"""
        # Mock IoT data query response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": [
                {"temperature": 20.5, "timestamp": 1000},
                {"temperature": 21.0, "timestamp": 2000},
                {"temperature": 21.5, "timestamp": 3000},
                {"temperature": 22.0, "timestamp": 4000},
                {"temperature": 23.5, "timestamp": 5000}
            ]
        }
        mock_post.return_value = mock_response
        
        trend = await monitoring_agent.analyze_temperature_trends("room-1")
        
        assert trend["trend"] == "increasing"
        assert trend["average_temp"] == 21.7
        assert trend["rate_of_change"] > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, monitoring_agent):
        """Test anomaly detection in sensor data"""
        sensor_data = [
            {"temperature": 20.5, "timestamp": 1000},
            {"temperature": 21.0, "timestamp": 2000},
            {"temperature": 45.0, "timestamp": 3000},  # Anomaly
            {"temperature": 21.5, "timestamp": 4000},
            {"temperature": 22.0, "timestamp": 5000}
        ]
        
        anomalies = monitoring_agent.detect_anomalies(sensor_data)
        
        assert len(anomalies) == 1
        assert anomalies[0]["temperature"] == 45.0
        assert anomalies[0]["anomaly_score"] > 0.8


class TestControlAgent:
    """Test suite for ControlAgent"""
    
    @pytest.fixture
    def control_agent(self):
        return ControlAgent("control-1", "http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_control_agent_capabilities(self, control_agent):
        """Test control agent has correct capabilities"""
        capabilities = control_agent.get_capabilities()
        assert "device_control" in capabilities
        assert "automation" in capabilities
        assert "scene_management" in capabilities
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_automated_lighting_control(self, mock_post, control_agent):
        """Test automated lighting based on motion detection"""
        # Mock motion detection query
        motion_response = Mock()
        motion_response.status_code = 200
        motion_response.json.return_value = {
            "status": "success",
            "data": {"motion_detected": True, "location": "living_room"}
        }
        
        # Mock control command response
        control_response = Mock()
        control_response.status_code = 200
        control_response.json.return_value = {
            "status": "command_sent",
            "device_id": "light-1"
        }
        
        mock_post.side_effect = [motion_response, control_response]
        
        result = await control_agent.automated_lighting("living_room")
        
        assert result["action"] == "lights_on"
        assert result["reason"] == "motion_detected"
        
        # Verify two calls were made
        assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_scene(self, control_agent):
        """Test creating and storing scenes"""
        scene_config = {
            "name": "movie_night",
            "devices": {
                "light-1": {"brightness": 20},
                "light-2": {"brightness": 0},
                "tv-1": {"power": "on"}
            }
        }
        
        await control_agent.create_scene("movie_night", scene_config)
        
        assert "movie_night" in control_agent.scenes
        assert control_agent.scenes["movie_night"] == scene_config


class TestAnalyticsAgent:
    """Test suite for AnalyticsAgent"""
    
    @pytest.fixture
    def analytics_agent(self):
        return AnalyticsAgent("analytics-1", "http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_analytics_agent_capabilities(self, analytics_agent):
        """Test analytics agent has correct capabilities"""
        capabilities = analytics_agent.get_capabilities()
        assert "data_analysis" in capabilities
        assert "prediction" in capabilities
        assert "reporting" in capabilities
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_energy_consumption_analysis(self, mock_post, analytics_agent):
        """Test energy consumption analysis"""
        # Mock device data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": [
                {"device_id": "switch-1", "power_usage": 50, "duration": 3600},
                {"device_id": "switch-2", "power_usage": 100, "duration": 1800},
                {"device_id": "switch-3", "power_usage": 75, "duration": 7200}
            ]
        }
        mock_post.return_value = mock_response
        
        analysis = await analytics_agent.analyze_energy_consumption()
        
        assert "total_consumption" in analysis
        assert "per_device" in analysis
        assert "recommendations" in analysis
        assert analysis["total_consumption"] > 0
    
    @pytest.mark.asyncio
    async def test_predict_temperature(self, analytics_agent):
        """Test temperature prediction based on historical data"""
        historical_data = [
            {"temperature": 20.0, "timestamp": 0},
            {"temperature": 21.0, "timestamp": 3600},
            {"temperature": 22.0, "timestamp": 7200},
            {"temperature": 23.0, "timestamp": 10800}
        ]
        
        prediction = analytics_agent.predict_temperature(historical_data, hours_ahead=1)
        
        assert "predicted_temperature" in prediction
        assert "confidence" in prediction
        assert 23.0 <= prediction["predicted_temperature"] <= 25.0
        assert 0.0 <= prediction["confidence"] <= 1.0
