
from flask import Blueprint

module1_bp = Blueprint("module1", __name__)

from . import routes
__all__ = ["module1_bp"]