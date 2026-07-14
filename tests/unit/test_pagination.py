import pytest
from app.api.v1.common.pagination import paginate_query, apply_sorting


class TestPagination:
    """Тесты пагинации"""
    
    def test_paginate_query_page_based(self, app, db_extension, user):
        """Тест page-based пагинации"""

        from app.domain.models.user.entities import User
        from app.api.v1.users.schemas import UserSchema
        
        with app.test_request_context('/?page=1&per_page=10'):
            query = User.query
            result = paginate_query(query, UserSchema())
            
            assert 'items' in result
            assert 'meta' in result
            assert result['meta']['page'] == 1
            assert result['meta']['per_page'] == 10
    
    def test_paginate_query_offset_based(self, app, db_extension, user):
        """Тест offset-based пагинации"""
        
        from app.domain.models.user.entities import User
        from app.api.v1.users.schemas import UserSchema
        
        with app.test_request_context('/?offset=0&limit=10'):
            query = User.query
            result = paginate_query(query, UserSchema())
            
            assert 'items' in result
            assert 'meta' in result
            assert result['meta']['offset'] == 0
            assert result['meta']['limit'] == 10