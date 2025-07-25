#!/usr/bin/env python3
"""
Log & Metrics Analysis Tool

A command-line tool that uses the Strands Agent SDK to analyze incident logs and metrics.
"""
import requests
from typing import Dict, Union

# Third-party imports
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands_tools import think

API_BASE_URL = "http://127.0.0.1:8000"


@tool
def get_logs_and_metrics(incident_id: str) -> Union[Dict, str]:
    """Fetches logs and metrics for a given incident ID from the simulation API."""
    try:
        if not incident_id.strip():
            return {"status": "error", "message": "Incident ID is required"}

        url = f"{API_BASE_URL}/log_metrics_retrieval/{incident_id}"
        print(f"Querying logs and metrics from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API call failed: {str(e)}. Make sure the incident_api.py server is running."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


def create_initial_messages():
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [{"text": "Hello, I need help analyzing logs and metrics for an incident."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help. Please provide an incident ID."
                }
            ],
        },
    ]


def create_log_metrics_agent():
    """Create and configure the log and metrics analysis agent."""
    return Agent(
        agent_id="log_metrics_agent",
        system_prompt="""You are a log and metrics analysis specialist for on-call engineering.
        Your task is to:
        1. Use 'get_logs_and_metrics' with an incident ID to fetch data.
        2. Analyze the logs for critical errors or warnings.
        3. Analyze the metrics for anomalies (e.g., high CPU, latency spikes, high error rates).
        4. Summarize your findings, correlating logs with metric anomalies to suggest a potential cause.""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_logs_and_metrics, think],
    )


def main():
    """Main function to run the log and metrics analysis tool."""
    log_metrics_agent = create_log_metrics_agent()
    log_metrics_agent.messages = create_initial_messages()

    print("\n📉 Log & Metrics Analyzer 📈\n")

    while True:
        query = input("\nEnter Incident ID> ").strip()
        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nAnalyzing...\n")
        try:
            response = log_metrics_agent(f"Analyze logs and metrics for incident: {query}")
            print(f"Analysis Results:\n{response}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")
        finally:
            log_metrics_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()