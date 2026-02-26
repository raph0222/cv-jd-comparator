import logging
import time
from contextlib import contextmanager
from typing import Iterator


logger = logging.getLogger(__name__)


@contextmanager
def trace_span(span_name: str, request_id: str = "") -> Iterator[None]:
    start = time.perf_counter()
    logger.info("trace_start span=%s request_id=%s", span_name, request_id)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("trace_end span=%s request_id=%s elapsed_seconds=%.4f", span_name, request_id, elapsed)
