import time
import requests
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from fastapi import FastAPI

from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


# Configure OpenTelemetry
resource = Resource.create({
    "service.name": "order-api",
    "deployment.environment.name": "lab",
    "service.version": "1.0.0",
})

trace.set_tracer_provider(
    TracerProvider(resource=resource)
)

tracer_provider = trace.get_tracer_provider()

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True,
)

tracer_provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)


# Create FastAPI application
app = FastAPI()

# Automatically instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)


@app.get("/")
def root():
    return {"message": "Hello from my OpenTelemetry lab"}


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        if order_id == 500:
            span.set_attribute("order.status", "failed")
            raise ValueError("Simulated order processing failure")

        if order_id == 999:
            span.set_attribute("order.status", "delayed")
            time.sleep(5)

        if order_id == 408:
            span.set_attribute("order.status", "timeout")
            time.sleep(30)

        inventory_response = requests.get(
                f"http://localhost:8001/inventory/{order_id}"
        )

        span.set_attribute(
            "inventory.status_code",
            inventory_response.status_code
        )

        span.set_attribute("order.status", "processing")

        return {
            "order_id": order_id,
            "status": "processing",
            "inventory": inventory_response.json()
        }
