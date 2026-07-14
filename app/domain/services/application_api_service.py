from flask import jsonify
from ..models.application.entities import Application, Diagnosis
from ...core.extensions import db

class ApplicationApiService:
    @staticmethod
    def get_diagnoses():
        diagnoses = Diagnosis.query.all()
        return jsonify([{'id': d.id, 'text': d.name} for d in diagnoses])

    @staticmethod
    def get_gdu_list():
        groups = db.session.query(Application.gdu).distinct().all()
        return jsonify([{'id': g[0], 'text': g[0]} for g in groups if g[0]])
    