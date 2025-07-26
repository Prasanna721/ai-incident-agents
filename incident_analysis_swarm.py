#!/usr/bin/env python3
"""
Incident Analysis Swarm Agent

A collaborative swarm of specialized agents for comprehensive incident analysis.
"""

# Standard library imports
import time
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Third-party imports
from strands import Agent
from strands.models import BedrockModel
from strands_tools import think, http_request
from strands_tools.swarm import Swarm, SwarmAgent

# Local imports
from incident_search_agent import get_incident_details, create_incident_search_agent
from log_metrics_agent import get_logs_and_metrics, create_log_metrics_agent
from code_retrieval_agent import get_code_context, create_code_retrieval_agent


class IncidentAnalysisSwarm:
    """A collaborative swarm of specialized agents for incident analysis."""

    def __init__(self):
        """Initialize the swarm with specialized agents."""
        # Initialize Swarm with Nova Pro model
        self.swarm = Swarm(
            task="Analyze production incident with multiple specialized agents",
            coordination_pattern="collaborative",
        )

        # Create SwarmAgent instances with correct parameters
        self.search_agent = SwarmAgent(
            agent_id="incident_search_agent",
            system_prompt="""You are an incident discovery specialist in the swarm.
            Your role is to:
            1. Use get_incident_details to find incident information from user queries
            2. Extract incident ID and build ID for other agents
            3. Share incident metadata with the swarm
            4. Ensure accuracy of incident identification""",
            shared_memory=self.swarm.shared_memory,
        )
        self.search_agent.tools = [get_incident_details, think]

        self.logs_agent = SwarmAgent(
            agent_id="log_metrics_agent",
            system_prompt=create_log_metrics_agent().system_prompt,
            shared_memory=self.swarm.shared_memory,
        )
        self.logs_agent.tools = [get_logs_and_metrics, http_request, think]

        self.code_agent = SwarmAgent(
            agent_id="code_retrieval_agent",
            system_prompt=create_code_retrieval_agent().system_prompt,
            shared_memory=self.swarm.shared_memory,
        )
        self.code_agent.tools = [get_code_context, http_request, think]

        # Add agents to swarm with their system prompts
        self.swarm.add_agent(
            self.search_agent,
            system_prompt="""You are the incident search coordinator in the swarm.
            Use get_incident_details to find and verify incident information.
            Share verified incident data with other agents.
            Focus on accuracy and completeness of incident identification.""",
        )

        self.swarm.add_agent(
            self.logs_agent,
            system_prompt="""You are a telemetry analysis specialist in the swarm.
            Analyze logs, metrics, and system performance data.
            Share telemetry insights with other agents.
            Focus on identifying anomalies and correlation patterns.""",
        )

        self.swarm.add_agent(
            self.code_agent,
            system_prompt="""You are a code change analysis specialist in the swarm.
            Analyze deployments, code changes, and build information.
            Share code analysis insights with other agents.
            Focus on identifying potential code-related root causes.""",
        )

    def analyze_incident(self, query: str) -> Dict[str, Any]:
        """Run the swarm analysis for an incident."""
        try:
            # Initialize shared memory with query
            self.swarm.shared_memory.store("query", query)

            # Phase 1: Search for incident details
            print("\\nPhase 1: Searching for incident details...")
            search_result = self.swarm.process_phase()

            if search_result:
                # Extract incident details from search result
                incident_info = None
                for result in search_result:
                    if result.get("agent_id") == "incident_search_agent":
                        incident_info = result.get("result", {}).get("content", [{}])[0].get("text", "")
                        break

                if incident_info:
                    # Parse and store incident data
                    self.swarm.shared_memory.store("incident_details", incident_info)
                    print(f"Found incident details: {incident_info}")

                    # Phase 2: Parallel Analysis
                    print("\\nPhase 2: Analyzing logs, metrics, and code changes...")
                    analysis_results = self.swarm.process_phase()

                    return {
                        "status": "success",
                        "incident_search": search_result,
                        "analysis_results": analysis_results,
                        "shared_memory": self.swarm.shared_memory.get_all_knowledge(),
                    }
                else:
                    return {"status": "error", "message": "Failed to extract incident details"}
            else:
                return {"status": "error", "message": "Failed to find incident details"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


def create_orchestration_agent() -> Agent:
    """Create the main orchestration agent that coordinates the swarm."""
    swarm_instance = IncidentAnalysisSwarm()
    
    return Agent(
        system_prompt="""You are an expert On-Call Engineering Lead and incident orchestrator. Your role is to:
        1. Coordinate the swarm of specialized agents for incident analysis
        2. Monitor the analysis process across all agents
        3. Integrate and synthesize all findings from the swarm
        4. Present a comprehensive incident analysis report
        
        When analyzing results, structure the report as follows:
        1. Incident Overview
           - Incident ID and basic details
           - Service impact and severity
           - Timeline and status
        
        2. Telemetry Analysis
           - Log analysis findings
           - Metrics and performance data
           - System health indicators
           - Error patterns and anomalies
        
        3. Code Change Analysis
           - Recent deployments and builds
           - Code changes and modifications
           - Deployment status and tests
           - Rollback assessment
        
        4. Root Cause Analysis
           - Correlation of telemetry and code changes
           - Most likely root cause hypothesis
           - Contributing factors
        
        5. Incident Response Recommendations
           - Immediate action items
           - Rollback decisions
           - Monitoring and alerting improvements
           - Prevention measures
           - Next steps and escalation path""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[swarm_instance.analyze_incident, think, http_request],
    )


def create_initial_messages() -> List[Dict]:
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [{"text": "We have a production incident that needs analysis."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help analyze the production incident. Please describe the issue you're experiencing or provide any incident details you have."
                }
            ],
        },
    ]


def main():
    """Main function to run the incident analysis swarm."""
    # Create the orchestration agent
    orchestration_agent = create_orchestration_agent()

    # Initialize messages for the orchestration agent
    orchestration_agent.messages = create_initial_messages()

    print("\\n🚨 Incident Analysis Swarm 🤖\\n")

    while True:
        query = input("\\nDescribe the production incident (or 'exit' to quit)> ")

        if query.lower() == "exit":
            print("\\nGoodbye! 👋")
            break

        print("\\nInitiating swarm analysis...\\n")

        try:
            # Create the user message with proper Nova format
            user_message = {
                "role": "user",
                "content": [
                    {
                        "text": f"Please analyze this incident and provide a comprehensive report: {query}"
                    }
                ],
            }

            # Add message to conversation
            orchestration_agent.messages.append(user_message)

            # Get response
            response = orchestration_agent(user_message["content"][0]["text"])

            # Format and print response
            if isinstance(response, dict) and "content" in response:
                print("\\nIncident Analysis Results:")
                for content in response["content"]:
                    if "text" in content:
                        print(content["text"])
            else:
                print(f"\\nIncident Analysis Results:\\n{response}\\n")

        except Exception as e:
            print(f"Error: {str(e)}\\n")
            if "ThrottlingException" in str(e):
                print("Rate limit reached. Waiting 5 seconds before retry...")
                time.sleep(5)
                continue
        finally:
            # Reset conversation after each query to maintain clean context
            orchestration_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()