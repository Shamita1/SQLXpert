
from flask import request, jsonify

from . import module1_bp
from .service import execute_query


@module1_bp.route("/execute", methods=["POST"])
def run_query():
    """Receive and execute a SQL query."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be valid JSON."
        }), 400

    query = data.get("query")

    if not isinstance(query, str) or not query.strip():
        return jsonify({
            "success": False,
            "message": "The query field is required."
        }), 400

    result = execute_query(query)

    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result), 200
