"""
Distributed tracing (OpenTelemetry) setup for INEsCape.

Tracing is opt-in: setup_tracing() is a no-op unless
settings.OTEL_EXPORTER_OTLP_ENDPOINT is set, so local development and
tests never need an OTLP collector running. When enabled, it exports
spans for every HTTP request (via FastAPI auto-instrumentation) and
every SQLAlchemy query, so a slow or failing request in production can
be traced across the API/DB boundary instead of relying on logs alone.
"""
import logging

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing(app: FastAPI) -> None:
    """Wire up OpenTelemetry tracing for the app, if configured."""
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info(
            "Distributed tracing disabled (set OTEL_EXPORTER_OTLP_ENDPOINT "
            "to an OTLP collector URL, e.g. http://otel-collector:4318, to enable)."
        )
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT is set but the opentelemetry packages "
            "are not installed (see requirements.txt); tracing stays disabled."
        )
        return

    resource = Resource.create(
        {SERVICE_NAME: settings.APP_NAME, "service.version": settings.APP_VERSION}
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    try:
        SQLAlchemyInstrumentor().instrument()
    except Exception as e:
        # Don't let instrumentation of the DB layer take down the app -
        # request tracing is still useful without it.
        logger.warning("SQLAlchemy tracing instrumentation failed: %s", e)

    logger.info(
        "Distributed tracing enabled, exporting to %s",
        settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    )
