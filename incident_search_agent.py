#!/usr/bin/env python3
"""
Incident Search Tool

A tool that uses the Strands Agent SDK to find initial incident details.
"""

import datetime as dt
from typing import Dict, Union

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think


@tool
def get_incident_details(user_query: str) -> Union[Dict, str]:
    """
    Finds incident details like ID and build ID from a user query.
    This is a mock tool that returns a predefined incident.
    """
    try:
        if not user_query:
            return {"status": "error", "message": "User query is required"}

        # In a real system, this would query a ticketing system like JIRA or PagerDuty
        print(f"Searching for incident related to: '{user_query}'")
        mock_incident = {
            "incidentId": "INC-2024-4567",
            "build_id": "build-prod-1.2.3-a1b2c3d4",
            "summary": "High latency and errors on checkout-service",
            "priority": "High",
            "timestamp": dt.datetime.now().isoformat(),
        }

        return {
            "status": "success",
            "data": mock_incident,
        }

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
    return Agent(
        agent_id="incident_search_agent",
        system_prompt="""You are an incident discovery specialist. Your job is to:
        1. Understand the user's report about a production issue.
        2. Use the 'get_incident_details' tool to find the official incident ID and the associated build ID.
        3. Extract and present the key details of the incident: ID, summary, priority, and build ID.""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_incident_details, think],
    )


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