#!/usr/bin/env python3
"""
Code Retrieval and Analysis Tool

A tool that uses the Strands Agent SDK to analyze code changes for an incident.
"""
import requests
from typing import Dict, Union

# Third-party imports
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands_tools import think, http_request

API_BASE_URL = "http://127.0.0.1:8000"


@tool
def get_code_context(build_id: str) -> Union[Dict, str]:
    """Fetches code change context for a given build ID from the simulation API."""
    try:
        if not build_id.strip():
            return {"status": "error", "message": "Build ID is required"}

        url = f"{API_BASE_URL}/code_retrieval_tool/{build_id}"
        print(f"Querying code context from: {url}")
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
            "content": [{"text": "Hello, I need to analyze code changes for a build."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help analyze code changes. Please provide a build ID."
                }
            ],
        },
    ]


def create_code_retrieval_agent():
    """Create and configure the code retrieval agent."""
    agent = Agent(
        agent_id="code_retrieval_agent",
        system_prompt="""You are a code analysis specialist for incident response. Follow these steps:

<input>
When you receive a build ID:
1. Use 'get_code_context' to fetch recent code changes and deployment info
2. Analyze file changes for potential incident causes
3. Review deployment metadata and test results
4. Provide structured analysis in the format below
</input>

<output_format>
1. Deployment Overview:
   - Build Information
   - Services Affected
   - Deployment Status
   - Test Results

2. Code Change Analysis:
   - Critical File Changes
   - Risk Assessment
   - Breaking Changes Identified
   - Dependencies Modified

3. Incident Correlation:
   - Potential Root Causes
   - Timing Analysis
   - Impact Assessment

4. Rollback Assessment:
   - Rollback Feasibility
   - Risk Mitigation
   - Recovery Steps
</output_format>""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_code_context, http_request, think],
    )
    # Set unique name for Swarm compatibility
    agent.name = "code_retrieval_agent"
    return agent


def main():
    """Main function to run the code retrieval tool."""
    code_agent = create_code_retrieval_agent()
    code_agent.messages = create_initial_messages()

    print("\n💻 Code Retrieval & Analysis Tool 📄\n")

    while True:
        query = input("\nEnter Build ID> ").strip()
        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nAnalyzing code changes...\n")
        try:
            response = code_agent(f"Analyze code context for build: {query}")
            print(f"Analysis Results:\n{response}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")
        finally:
            code_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()