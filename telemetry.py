import logging

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_opentelemetry():
    # Resource identifies this service in Tempo/Grafana
    resource = Resource.create(
        {
            "service.name": "fastapi-demo",
            "service.version": "0.1.0",
        }
    )

    # Tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Exporter -> Alloy (OTLP gRPC)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True,
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint="http://localhost:4317",
                insecure=True,
            )
        )
    )

    handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=logger_provider,
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
