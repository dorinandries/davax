from prometheus_fastapi_instrumentator import Instrumentator

def setup_metrics(app):
    Instrumentator().instrument(app).expose(
        app, include_in_schema=False, endpoint="/api/v1/metrics"
    )