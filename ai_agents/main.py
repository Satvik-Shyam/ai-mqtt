"""
AI Agents Main Module

This module serves as the entry point for running the AI agents.
"""

import asyncio
import sys
import os
import argparse
import logging
from typing import List, Dict, Any

from .monitoring_agent import MonitoringAgent
from .control_agent import ControlAgent
from .analytics_agent import AnalyticsAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_agents(intermediary_url: str = None, agent_types: List[str] = None):
    """
    Run the specified AI agents.
    
    Args:
        intermediary_url (str): URL of the intermediary service
        agent_types (List[str]): List of agent types to run
    """
    # Get intermediary URL from environment if not specified
    if not intermediary_url:
        intermediary_url = os.getenv("INTERMEDIARY_URL", "http://localhost:8000")
        
    # Default to all agent types if not specified
    if not agent_types:
        agent_types = ["monitoring", "control", "analytics"]
        
    print(f"Starting AI agents with intermediary URL: {intermediary_url}")
    print(f"Agent types: {', '.join(agent_types)}")
    
    # Create agents
    agents = []
    
    if "monitoring" in agent_types:
        monitoring_agent = MonitoringAgent("Monitor-1", intermediary_url)
        agents.append(monitoring_agent)
        print(f"Created monitoring agent: {monitoring_agent.name} ({monitoring_agent.agent_id})")
        
    if "control" in agent_types:
        control_agent = ControlAgent("Control-1", intermediary_url)
        agents.append(control_agent)
        print(f"Created control agent: {control_agent.name} ({control_agent.agent_id})")
        
    if "analytics" in agent_types:
        analytics_agent = AnalyticsAgent("Analytics-1", intermediary_url)
        agents.append(analytics_agent)
        print(f"Created analytics agent: {analytics_agent.name} ({analytics_agent.agent_id})")
    
    # Start all agents
    for agent in agents:
        await agent.start()
        
    print(f"All {len(agents)} agents started")
    
    try:
        # Run forever
        while True:
            await asyncio.sleep(60)
            print(f"Agents running... ({len(agents)} active)")
    except KeyboardInterrupt:
        print("Stopping agents...")
    finally:
        # Stop all agents
        for agent in agents:
            await agent.stop()
            
        print("All agents stopped")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AI Agents Runner")
    parser.add_argument("--intermediary-url", type=str, default=None,
                        help="URL of the intermediary service (default: from environment or http://localhost:8000)")
    parser.add_argument("--agent-types", type=str, nargs="+", choices=["monitoring", "control", "analytics"],
                        default=None, help="Types of agents to run (default: all)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_agents(
        intermediary_url=args.intermediary_url,
        agent_types=args.agent_types
    ))
