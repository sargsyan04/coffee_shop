import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging_config import get_logger

logger = get_logger("requests")


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        client_ip = get_client_ip(request)
        request.state.client_ip = client_ip
        start_time = time.perf_counter()

        logger.info(
            "request_started | id=%s | method=%s | path=%s | client_ip=%s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_failed | id=%s | method=%s | path=%s | client_ip=%s | duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                client_ip,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        log_level = logger.warning if response.status_code >= 400 else logger.info
        log_level(
            "request_finished | id=%s | method=%s | path=%s | client_ip=%s | status=%s | duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            client_ip,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
