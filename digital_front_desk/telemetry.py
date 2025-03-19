from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from typing import Optional

class TelemetryManager:
    _instance: Optional['TelemetryManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Create resource
        resource = Resource.create({
            "service.name": "digital-front-desk",
            "service.version": "1.0.0"
        })

        # Set up tracing with Zipkin
        trace_provider = TracerProvider(resource=resource)
        zipkin_exporter = ZipkinExporter(
            endpoint="http://localhost:9411/api/v2/spans",
        )
        trace_provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
        trace.set_tracer_provider(trace_provider)
        self.tracer = trace.get_tracer(__name__)

        # Set up metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint="http://localhost:4317")
        )
        metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(metric_provider)
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.request_counter = self.meter.create_counter(
            name="front_desk.requests",
            description="Number of requests processed",
            unit="1"
        )

        self.response_time = self.meter.create_histogram(
            name="front_desk.response_time",
            description="Response time for processing requests",
            unit="ms"
        )

        self.triage_scores = self.meter.create_histogram(
            name="front_desk.triage_scores",
            description="Distribution of triage scores",
            unit="1"
        )

    def record_request(self, channel_type: str):
        self.request_counter.add(1, {"channel": channel_type})

    def record_response_time(self, duration_ms: float, channel_type: str):
        self.response_time.record(duration_ms, {"channel": channel_type})

    def record_triage_score(self, score: float):
        self.triage_scores.record(score)

# Global instance
telemetry = TelemetryManager() 