#!/usr/bin/env python3
"""
Incident Search Tool

A tool that uses the Strands Agent SDK to find initial incident details.
"""

import datetime as dt
import requests
from typing import Dict, Union

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think, http_request

API_BASE_URL = "http://127.0.0.1:8000"


@tool
def get_incident_details(user_query: str) -> Union[Dict, str]:
    """
    Finds incident details like ID and build ID from a user query.
    This searches through available incidents and returns the most relevant one.
    """
    try:
        if not user_query:
            return {"status": "error", "message": "User query is required"}

        print(f"Searching for incident related to: '{user_query}'")
        
        # Get list of available incidents
        try:
            response = requests.get(f"{API_BASE_URL}/incidents", timeout=10)
            response.raise_for_status()
            incidents_list = response.json()
            
            if incidents_list.get("status") != "success":
                return {"status": "error", "message": "Failed to retrieve incidents list"}
            
            # For demo purposes, return the first incident
            # In a real system, you would implement smart matching based on the query
            available_incidents = incidents_list["data"]["incidents"]
            if not available_incidents:
                return {"status": "error", "message": "No incidents found"}
            
            # Get details for the first incident (in real system, implement intelligent matching)
            incident_id = available_incidents[0]
            
            # Mock build ID mapping - in real system this would come from incident correlation
            mock_incident = {
                "incidentId": incident_id,
                "build_id": "BUILD-2024-0425",  # This would be dynamically determined
                "summary": "Production incident requiring investigation",
                "priority": "High",
                "timestamp": dt.datetime.now().isoformat(),
            }

            return {
                "status": "success",
                "data": mock_incident,
            }
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"API call failed: {str(e)}. Make sure the incident_api.py server is running."}

    except Exception as e:
        return {"status": "error", "message": f"Error fetching incident details: {str(e)}"}


def create_initial_messages():
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [{"text": "Hello, I need help analyzing an incident."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help. Please describe the incident or provide an incident ID."
                }
            ],
        },
    ]


def create_incident_search_agent():
    """Create and configure the incident search agent."""
    agent = Agent(
        agent_id="incident_search_agent",
        system_prompt="""You are an incident discovery specialist. Your job is to:
        1. Understand the user's report about a production issue.
        2. Use the 'get_incident_details' tool to find the official incident ID and the associated build ID.
        3. Extract and present the key details of the incident: ID, summary, priority, and build ID.""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_incident_details, think],
    )
    # Set unique name for Swarm compatibility
    agent.name = "incident_search_agent"
    return agent


def main():
    """Main function to run the incident search tool."""
    incident_agent = create_incident_search_agent()
    incident_agent.messages = create_initial_messages()

    print("\n🔍 Incident Search Tool 🚨\n")

    while True:
        query = input("\nDescribe the incident> ").strip()
        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nSearching for incident...\n")
        try:
            response = incident_agent(f"Find the incident for: {query}")
            print(f"Incident Details:\n{response}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")
        finally:
            incident_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()