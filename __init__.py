"""
On-Call Assistant Tools

A collection of tools for incident analysis using the Strands Agent SDK.
"""

# Import modules
from . import log_metrics_agent
from . import code_retrieval_agent
from . import incident_search_agent
from . import on_call_assistant_swarm

# Import specific functions and classes for convenience
from .log_metrics_agent import get_logs_and_metrics, create_log_metrics_agent
from .code_retrieval_agent import get_code_context, create_code_retrieval_agent
from .incident_search_agent import get_incident_details, create_incident_search_agent
from .on_call_assistant_swarm import (
    IncidentAnalysisSwarm,
    create_orchestration_agent,
)

__all__ = [
    # Modules
    "log_metrics_agent",
    "code_retrieval_agent",
    "incident_search_agent",
    "on_call_assistant_swarm",
    # Functions
    "get_logs_and_metrics",
    "get_code_context",
    "get_incident_details",
    # Agent creators
    "create_log_metrics_agent",
    "create_code_retrieval_agent",
    "create_incident_search_agent",
    "create_orchestration_agent",
    # Classes
    "IncidentAnalysisSwarm",
]