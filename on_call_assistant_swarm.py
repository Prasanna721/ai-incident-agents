#!/usr/bin/env python3
"""
On-Call Assistant Swarm Agent

A collaborative swarm of specialized agents for comprehensive incident analysis.
"""

# Standard library imports
from typing import Dict, Any, List

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think
from strands_tools.swarm import Swarm

# Local imports  
from log_metrics_agent import create_log_metrics_agent
from code_retrieval_agent import create_code_retrieval_agent  
from incident_search_agent import create_incident_search_agent, get_incident_details


class IncidentAnalysisSwarm:
    """A collaborative swarm of specialized agents for incident analysis."""

    def __init__(self):
        search_agent = create_incident_search_agent()
        log_metrics_agent = create_log_metrics_agent()
        code_agent = create_code_retrieval_agent()
        
        # Try setting name property to ensure unique node IDs
        search_agent.name = "incident_search_agent"
        log_metrics_agent.name = "log_metrics_agent" 
        code_agent.name = "code_retrieval_agent"
        
        self.search_agent = search_agent
        self.log_metrics_agent = log_metrics_agent
        self.code_agent = code_agent

        swarm_nodes = [
            self.search_agent,
            self.log_metrics_agent,
            self.code_agent,
        ]

        self.swarm = Swarm(nodes=swarm_nodes)

    @tool
    def analyze_incident(self, query: str) -> Dict[str, Any]:
        try:
            # Phase 1: Manually find incident details to get critical IDs.
            print("\nPhase 1: Finding Incident Details...")
            incident_search_result = get_incident_details(query)

            if incident_search_result.get("status") != "success":
                return {"status": "error", "message": "Could not find incident details."}

            incident_data = incident_search_result["data"]
            incident_id = incident_data["incidentId"]
            build_id = incident_data["build_id"]

            # Store the retrieved IDs in shared memory for the next phase.
            self.swarm.shared_memory.store("incident_id", incident_id)
            self.swarm.shared_memory.store("build_id", build_id)
            self.swarm.shared_memory.store("incident_summary", incident_data)
            
            print(f"Found Incident ID: {incident_id}, Build ID: {build_id}")
            
            # Phase 2: Run the analysis agents in parallel.
            print("\nPhase 2: Analyzing logs, metrics, and code changes in parallel...")
            analysis_results = self.swarm.process_phase(
                agent_ids=["log_metrics_agent", "code_retrieval_agent"]
            )

            return {
                "status": "success",
                "analysis_results": analysis_results,
                # "shared_memory": self.swarm.shared_memory.get_all_knowledge(),
            }

        except Exception as e:
            print(f"An exception occurred during swarm execution: {e}")
            return {"status": "error", "message": str(e)}


def create_orchestration_agent() -> Agent:
    """Create the main orchestration agent that coordinates the swarm and synthesizes a report."""
    swarm_instance = IncidentAnalysisSwarm()
    
    orchestrator = Agent(
        # Manually set the ID for the orchestrator as well for good practice.
        agent_id="orchestrator_agent",
        system_prompt="""You are an expert On-Call Engineering Lead. Your role is to:
        1. Receive a user query about a production incident.
        2. Call the `analyze_incident` tool with the user's query to coordinate a swarm of specialists.
        3. Synthesize the information from the `shared_memory` key in the tool's output into a single, structured incident report.
        4. Present a final, comprehensive report that outlines the incident, potential causes, and recommended next steps.

        <output_format>
        # Incident Report: [Incident ID from shared_memory]

        ## 1. Incident Summary
        - **Priority**: [Value from 'priority' in incident_summary]
        - **Summary**: [Value from 'summary' in incident_summary]

        ## 2. Telemetry Analysis
        - **Key Findings**: [Summarize the output from the 'log_metrics_agent' found in the 'analysis_results']

        ## 3. Code Change Analysis
        - **Key Findings**: [Summarize the output from the 'code_retrieval_agent' found in the 'analysis_results']

        ## 4. Overall Assessment & Next Steps
        - **Hypothesis**: Based on telemetry and code analysis, state the most likely root cause.
        - **Recommendation**: Suggest immediate actions (e.g., rollback build, restart service, escalate).
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