#!/usr/bin/env python3
"""
On-Call Assistant Swarm Agent

A collaborative swarm of specialized agents for comprehensive incident analysis.
Improved version based on finance assistant swarm pattern.
"""

# Standard library imports
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think, http_request
from strands_tools.swarm import Swarm

# Local imports  
from log_metrics_agent import create_log_metrics_agent, get_logs_and_metrics
from code_retrieval_agent import create_code_retrieval_agent, get_code_context
from incident_search_agent import create_incident_search_agent, get_incident_details
from memory.shared_memory import create_shared_memory


class IncidentAnalysisSwarm:
    """A collaborative swarm of specialized agents for incident analysis."""

    def __init__(self):
        """Initialize the swarm with specialized agents."""
        # Create individual agents
        self.search_agent = create_incident_search_agent()
        self.logs_agent = create_log_metrics_agent()
        self.code_agent = create_code_retrieval_agent()
        
        # Set unique names/IDs for the agents
        self.search_agent.agent_id = "incident_search_agent"
        self.logs_agent.agent_id = "log_metrics_agent" 
        self.code_agent.agent_id = "code_retrieval_agent"
        
        # Create nodes list for the swarm
        swarm_nodes = [
            self.search_agent,
            self.logs_agent,
            self.code_agent,
        ]

        # Initialize Swarm with the agents
        self.swarm = Swarm(nodes=swarm_nodes)
        
        # Initialize shared memory for incident and analysis data storage
        try:
            self.swarm.shared_memory = create_shared_memory()
            print("✅ Shared memory initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize shared memory: {e}")
            print("   Swarm will continue without memory persistence")
            self.swarm.shared_memory = None

    @tool
    def analyze_incident(self, query: str) -> Dict[str, Any]:
        try:
            # Phase 1: Find incident details to get critical IDs.
            print("\nPhase 1: Finding Incident Details...")
            incident_search_result = get_incident_details(query)

            if incident_search_result.get("status") != "success":
                return {"status": "error", "message": "Could not find incident details."}

            incident_data = incident_search_result["data"]
            incident_id = incident_data["incidentId"]
            build_id = incident_data["build_id"]

            # Store the retrieved IDs in shared memory for the next phase.
            if self.swarm.shared_memory:
                self.swarm.shared_memory.store("incident_id", incident_id)
                self.swarm.shared_memory.store("build_id", build_id)
                self.swarm.shared_memory.store("incident_summary", incident_data)
                self.swarm.shared_memory.store("query", query)
                print("📝 Incident data stored in shared memory")
            
            print(f"Found Incident ID: {incident_id}, Build ID: {build_id}")
            
            # Phase 2: Run the analysis agents manually
            print("\nPhase 2: Analyzing logs, metrics, and code changes...")
            
            # Run logs analysis
            logs_result = None
            try:
                logs_analysis = f"Analyze logs and metrics for incident: {incident_id}"
                logs_result = self.logs_agent(logs_analysis)
                print("✅ Logs analysis completed")
            except Exception as e:
                print(f"⚠️  Logs analysis failed: {e}")
            
            # Run code analysis
            code_result = None
            try:
                code_analysis = f"Analyze code context for build: {build_id}"
                code_result = self.code_agent(code_analysis)
                print("✅ Code analysis completed")
            except Exception as e:
                print(f"⚠️  Code analysis failed: {e}")

            # Get shared memory knowledge for the orchestrator
            shared_memory_data = {}
            if self.swarm.shared_memory:
                try:
                    shared_memory_data = self.swarm.shared_memory.get_all_knowledge()
                except:
                    shared_memory_data = {
                        "incident_id": incident_id,
                        "build_id": build_id,
                        "incident_summary": incident_data,
                        "query": query
                    }
            
            return {
                "status": "success",
                "incident_details": incident_data,
                "logs_analysis": logs_result,
                "code_analysis": code_result,
                "shared_memory": shared_memory_data,
            }

        except Exception as e:
            print(f"An exception occurred during swarm execution: {e}")
            return {"status": "error", "message": str(e)}


def create_orchestration_agent() -> Agent:
    """Create the main orchestration agent that coordinates the swarm and synthesizes a report."""
    swarm_instance = IncidentAnalysisSwarm()
    
    orchestrator = Agent(
        agent_id="orchestrator_agent",
        system_prompt="""You are an expert On-Call Engineering Lead and incident orchestrator. Your role is to:
        1. Receive a user query about a production incident
        2. Call the `analyze_incident` tool with the user's query to coordinate specialized agents
        3. Synthesize all findings into a comprehensive incident report
        4. Present actionable recommendations for incident resolution

        <output_format>
        # Incident Analysis Report

        ## 1. Incident Overview
        - **Incident ID**: [From incident_details]
        - **Build ID**: [From incident_details]
        - **Summary**: [From incident_details]
        - **Priority**: [From incident_details]
        - **Timestamp**: [From incident_details]

        ## 2. Telemetry Analysis
        - **Key Findings**: [Summarize logs_analysis results]
        - **Performance Issues**: [Highlight metrics anomalies]
        - **Error Patterns**: [Log analysis insights]

        ## 3. Code Change Analysis
        - **Key Findings**: [Summarize code_analysis results]
        - **Recent Changes**: [Code modifications]
        - **Deployment Status**: [Build information]

        ## 4. Root Cause Assessment
        - **Primary Hypothesis**: [Most likely cause based on evidence]
        - **Contributing Factors**: [Secondary issues]
        - **Evidence**: [Supporting data from analysis]

        ## 5. Recommended Actions
        - **Immediate Steps**: [Urgent actions needed]
        - **Rollback Decision**: [Whether to rollback and why]
        - **Monitoring**: [What to watch]
        - **Follow-up**: [Next steps]
        </output_format>""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[swarm_instance.analyze_incident, think],
    )
    return orchestrator


def create_initial_messages() -> List[Dict]:
    """Create initial conversation messages."""
    return [
        {"role": "user", "content": [{"text": "We have a production incident."}]},
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I am ready to help. Please describe the issue you are seeing."
                }
            ],
        },
    ]


def main():
    """Main function to run the on-call assistant swarm."""
    orchestration_agent = create_orchestration_agent()
    orchestration_agent.messages = create_initial_messages()

    print("\n🚨 On-Call Assistant Swarm 🤖\n")

    while True:
        query = input("\nDescribe the production issue (or 'exit' to quit)> ").strip()

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nInitiating swarm analysis...\n")
        try:
            response = orchestration_agent(query)
            print(f"\n--- Final Incident Report ---\n{response}\n")

        except Exception as e:
            print(f"An error occurred: {str(e)}\n")
        finally:
            orchestration_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()