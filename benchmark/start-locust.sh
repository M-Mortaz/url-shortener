#!/bin/bash
# Quick start script for Locust load testing with 8 workers

echo "Starting Locust Master and 8 Workers..."
echo "Locust UI will be available at: http://localhost:8089"
echo ""

# Start Locust master and scale workers to 8
docker compose up --build --scale locust-worker=8 locust-master locust-worker

