import requests
from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)
bp = Blueprint("dadata", __name__, url_prefix="/api/suggest")

@bp.route("/address", methods=["POST"])
def suggest_address():
    """Возвращает подсказки по адресу через DaData"""
    try:
        query = request.json.get("query", "").strip()
        
        if not query or len(query) < 2:
            return jsonify({"suggestions": []})

        api_key = current_app.config.get('DADATA_API_KEY')
        if not api_key:
            logger.warning("DADATA_API_KEY not configured")
            return jsonify({"suggestions": []})

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

        payload = {"query": query, "count": 5}

        # Увеличиваем таймаут и добавляем обработку ошибок
        resp = requests.post(
            "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        resp.raise_for_status()
        return jsonify(resp.json())

    except requests.exceptions.Timeout:
        logger.warning("DaData API timeout")
        return jsonify({"suggestions": []})
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"DaData API connection error: {str(e)}")
        return jsonify({"suggestions": []})
    except requests.exceptions.RequestException as e:
        logger.error(f"DaData API request error: {str(e)}")
        return jsonify({"suggestions": []})
    except Exception as e:
        logger.error(f"Unexpected error in suggest_address: {str(e)}")
        return jsonify({"suggestions": []}), 500
