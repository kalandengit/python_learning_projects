"""OpenTelemetry → OTLP collector. SLOs: API p95 < 500 ms, scan < 200 ms (§2)."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings

logger = logging.getLogger(__name__)

SLO_API_P95_MS = 500
SLO_SCAN_MS = 200


def setup_telemetry(app: FastAPI, settings: Settings, engine: AsyncEngine) -> None:
    if settings.otel_exporter_otlp_endpoint is None:
        logger.info("telemetry disabled (EMS_OTEL_EXPORTER_OTLP_ENDPOINT unset)")
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.env,
            "slo.api_p95_ms": SLO_API_P95_MS,
            "slo.scan_ms": SLO_SCAN_MS,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, tracer_provider=provider)
    logger.info("telemetry: OTLP export to %s", settings.otel_exporter_otlp_endpoint)
