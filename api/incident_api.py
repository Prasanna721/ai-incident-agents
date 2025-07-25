#!/usr/bin/env python3
"""
Incident Simulation API

A mock API server using FastAPI to simulate incident management tool endpoints.
This provides data for the On-Call Assistant Swarm.
"""

import datetime as dt
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Incident Simulation API",
    description="Mock API for fetching incident logs, metrics, and code context.",
    version="1.0.0",
)


@app.get("/log_metrics_retrieval/{incident_id}")
def get_log_metrics_retrieval(incident_id: str):
    """
    Simulates fetching logs and metrics for a given incident ID.
    """
    if not incident_id:
        raise HTTPException(status_code=400, detail="Incident ID is required")

    # Mock data
    return {
        "status": "success",
        "data": {
            "incidentId": incident_id,
            "service": "checkout-service-prod",
            "timestamp": dt.datetime.now().isoformat(),
            "logs": [
                "[ERROR] Timeout connecting to payment-gateway",
                "[WARN] High latency detected in process_payment",
                "[INFO] User 'user-123' initiated checkout",
                "[ERROR] Database connection pool exhausted",
            ],
            "metrics": {
                "cpu_utilization": "95%",
                "memory_usage": "89%",
                "api_latency_p99": "3500ms",
                "error_rate": "15%",
            },
        },
    }


@app.get("/code_retrieval_tool/{build_id}")
def get_code_retrieval_tool(build_id: str):
    """
    Simulates fetching code context for a given build ID.
    """
    if not build_id:
        raise HTTPException(status_code=400, detail="Build ID is required")

    # Mock data
    return {
        "status": "success",
        "data": {
            "build_id": build_id,
            "repository": "github.com/example/checkout-service",
            "commit_hash": "a1b2c3d4",
            "timestamp": (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(),
            "file_changes": [
                {
                    "file": "src/gateways/payment.py",
                    "change": "updated timeout from 5s to 2s",
                },
                {
                    "file": "src/main.py",
                    "change": "added new metrics for payment retries",
                },
            ],
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting Incident Simulation API server...")
    print("Access endpoints at http://127.0.0.1:8000")
    print("Swagger UI: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)