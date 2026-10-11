from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


resource = Resource.create({
    "service.name": "inventory-api",
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

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)


@app.get("/inventory/{order_id}")
def check_inventory(order_id: int):
    with tracer.start_as_current_span("check_inventory") as span:
        span.set_attribute("order.id", order_id)

        return {
            "order_id": order_id,
            "available": True
        }
