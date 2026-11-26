from typing import Any

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status: int = 400
    code: str = "BAD_REQUEST"

    def __init__(
        self,
        message: str = "Bad request",
        fields: dict[str, str] | None = None,
        status: int | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.fields = fields
        if status:
            self.status = status
        if code:
            self.code = code


class ValidationError(ApiError):
    status = 400
    code = "VALIDATION"

    def __init__(self, fields: dict[str, str], message: str = "Validation failed"):
        super().__init__(message=message, fields=fields)


STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    500: "INTERNAL_ERROR",
}


def _json_error(
    status: int,
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
) -> tuple[Response, int]:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return jsonify({"error": error}), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(e: ApiError) -> tuple[Response, int]:
        return _json_error(e.status, e.code, e.message, e.fields)

    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException) -> tuple[Response, int]:
        status = e.code or 500
        code = STATUS_CODES.get(status, "ERROR")
        return _json_error(status, code, e.description or "Error")

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception) -> tuple[Response, int]:
        app.logger.exception("Unhandled exception", exc_info=e)
        return _json_error(500, "INTERNAL_ERROR", "Something went wrong on our end.")