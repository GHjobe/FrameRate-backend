"""Reports, moderation, fake-rating detection. Backlog."""
from flask import Blueprint

bp = Blueprint("moderation", __name__, url_prefix="/api/mod")