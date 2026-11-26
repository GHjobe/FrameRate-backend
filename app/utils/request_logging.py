import logging
import os
import time
from logging.handlers import RotatingFileHandler

from flask import Flask, Response, g, request, session


def init_request_logging(app: Flask) -> None:
    log_dir = os.path.join(os.path.dirname(app.root_path), "logs")
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(log_dir, "requests.log"),
        maxBytes=1_000_000,
        backupCount=5,
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

    request_logger = logging.getLogger("requests")
    request_logger.setLevel(logging.INFO)
    if not request_logger.handlers:
        request_logger.addHandler(handler)

    @app.before_request
    def _start_timer() -> None:
        g.request_start = time.perf_counter()

    @app.after_request
    def _log_request(response: Response) -> Response:
        start: float = g.get("request_start", time.perf_counter())
        duration_ms = (time.perf_counter() - start) * 1000
        user_id = str(session.get("user_id", "-"))
        # Only method, path (no query string), status, duration, user id.
        request_logger.info(
            "%s %s %s %.1fms user=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            user_id,
        )
        return response