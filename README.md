# FastAPI Observability

- OpenTelemetry Logs and Traces
- Instrumentation for FastAPI, Requests, SQLAlchemy and Logging
- Grafana Alloy: Telemetry Data Collector 
- Grafana Loki: Logs
- Grafana Tempo: Traces
- Grafana: Visualisation 
- Grafana Services orchestrated via Docker


# Try it out

Start the Grafana stack with
```
docker compose up -d
```
and then start the FastAPI app with
```
fastapi run dev main.py
```

