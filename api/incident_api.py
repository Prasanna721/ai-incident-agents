#!/usr/bin/env python3

import datetime as dt
import json
import os
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="AI Voice Company Incident API",
    description="Production incident management API for AI voice foundational model platform",
    version="2.0.0",
)

with open(os.path.join(os.path.dirname(__file__), 'ai_voice_incidents_data.json'), 'r') as f:
    INCIDENTS_DATA = json.load(f)


@app.get("/log_metrics_retrieval/{incident_id}")
def get_log_metrics_retrieval(incident_id: str):
    if not incident_id:
        raise HTTPException(status_code=400, detail="Incident ID is required")
    
    incident = INCIDENTS_DATA['incidents'].get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    return {
        "status": "success",
        "data": {
            "incidentId": incident_id,
            "title": incident['title'],
            "service": incident['service'],
            "severity": incident['severity'],
            "status": incident['status'],
            "timestamp": incident['created_at'],
            "resolved_at": incident.get('resolved_at'),
            "affected_customers": incident['affected_customers'],
            "description": incident['description'],
            "logs": incident['logs'],
            "metrics": incident['metrics'],
            "infrastructure": incident['infrastructure'],
            "root_cause": incident.get('root_cause'),
            "resolution": incident.get('resolution')
        },
    }


@app.get("/code_retrieval_tool/{build_id}")
def get_code_retrieval_tool(build_id: str):
    if not build_id:
        raise HTTPException(status_code=400, detail="Build ID is required")
    
    deployment = INCIDENTS_DATA['code_deployments'].get(build_id)
    if not deployment:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    return {
        "status": "success",
        "data": {
            "build_id": deployment['build_id'],
            "repository": deployment['repository'],
            "branch": deployment['branch'],
            "commit_hash": deployment['commit_hash'],
            "timestamp": deployment['timestamp'],
            "deployment_status": deployment['deployment_status'],
            "services_affected": deployment['services_affected'],
            "file_changes": deployment['file_changes'],
            "tests_passed": deployment['tests_passed'],
            "deployment_time_seconds": deployment['deployment_time_seconds'],
            "rollback_plan": deployment['rollback_plan']
        },
    }


@app.get("/incidents")
def list_incidents():
    return {
        "status": "success",
        "data": {
            "incidents": list(INCIDENTS_DATA['incidents'].keys()),
            "total_count": len(INCIDENTS_DATA['incidents'])
        }
    }

@app.get("/deployments")
def list_deployments():
    return {
        "status": "success",
        "data": {
            "deployments": list(INCIDENTS_DATA['code_deployments'].keys()),
            "total_count": len(INCIDENTS_DATA['code_deployments'])
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-voice-incident-api",
        "timestamp": dt.datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Starting AI Voice Company Incident API server...")
    print("Access endpoints at http://127.0.0.1:8000")
    print("Swagger UI: http://127.0.0.1:8000/docs")
    print("Available incidents: INC-2024-001, INC-2024-002, INC-2024-003")
    print("Available deployments: BUILD-2024-0425, BUILD-2024-0424, BUILD-2024-0423")
    uvicorn.run(app, host="127.0.0.1", port=8000)