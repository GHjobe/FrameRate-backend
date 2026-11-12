from flask import jsonify


def api_error(code, message, status, fields=None):
    """The JSON error shape the frontend reads: {"error": {"code", "message", "fields"}}."""
    return jsonify({"error": {"code": code, "message": message, "fields": fields or {}}}), status