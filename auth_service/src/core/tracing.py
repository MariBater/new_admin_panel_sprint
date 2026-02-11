from opentelemetry import trace
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def traced(endpoint_name=None):
    """Декоратор для трассировки функций."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = endpoint_name or func.__name__

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    logger.error(f"Error in {func.__name__}: {e}")
                    raise

        return async_wrapper

    return decorator


def traced_sync(endpoint_name=None):
    """Декоратор для синхронных функций."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = endpoint_name or func.__name__

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    logger.error(f"Error in {func.__name__}: {e}")
                    raise

        return wrapper

    return decorator
