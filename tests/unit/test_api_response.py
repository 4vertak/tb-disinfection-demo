import pytest
from app.api.v1.common.response import (
    success_response, created_response, no_content_response, 
    error_response, validation_error_response
)

class TestAPIResponse:
    def test_success_response(self, app):
        with app.test_request_context():
            response, status_code = success_response({'id': 1, 'name': 'Test'})
            assert status_code == 200
            assert response['data'] == {'id': 1, 'name': 'Test'}
            assert response['meta'] is None
            assert response['errors'] is None
    
    def test_created_response(self, app):
        with app.test_request_context():
            response, status_code = created_response({'id': 1})
            assert status_code == 201
            assert response['data'] == {'id': 1}
    
    def test_no_content_response(self, app):
        with app.test_request_context():
            response, status_code = no_content_response()
            assert status_code == 204
            assert response == ''
    
    def test_error_response(self, app):
        with app.test_request_context():
            response, status_code = error_response('Not found', 404)
            assert status_code == 404
            assert response['data'] is None
            assert response['errors'][0]['message'] == 'Not found'
            assert response['errors'][0]['code'] == 404
    
    def test_validation_error_response(self, app):
        with app.test_request_context():
            errors = {'login': ['Login is required']}
            response, status_code = validation_error_response(errors)
            assert status_code == 422
            assert response['errors'][0]['code'] == 422