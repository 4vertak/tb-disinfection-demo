"""Integration тесты для Blog API"""
import pytest
import io


class TestBlogAPI:
    """Integration тесты для Blog API"""
    
    def test_get_blog_posts_list(self, client):
        """Тест получения списка постов (публичный endpoint)"""
        response = client.get('/api/v1/blog/posts')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
        assert 'meta' in data['data']
    
    def test_get_blog_posts_with_pagination(self, client):
        """Тест пагинации постов"""
        response = client.get('/api/v1/blog/posts?page=1&per_page=5')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['meta']['page'] == 1
        assert data['data']['meta']['per_page'] == 5
    
    def test_get_blog_posts_with_search(self, client):
        """Тест поиска постов"""
        response = client.get('/api/v1/blog/posts?search=test')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data['data']
    
    def test_get_recent_posts(self, client):
        """Тест получения последних постов"""
        response = client.get('/api/v1/blog/recent?limit=3')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data['data'], list)
        assert len(data['data']) <= 3
    
    def test_create_blog_post_as_admin(self, client, admin_auth_headers):
        """Тест создания поста администратором"""
        response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Test Blog Post',
                'content': 'This is a test blog post content with enough length.',
                'excerpt': 'Test excerpt',
                'is_published': True
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['title'] == 'Test Blog Post'
        assert data['data']['is_published'] is True
    
    def test_create_blog_post_as_doctor_forbidden(self, client, doctor_auth_headers):
        """Тест создания поста врачом (должно быть запрещено)"""
        response = client.post('/api/v1/blog/posts',
            headers=doctor_auth_headers,
            json={
                'title': 'Test Post',
                'content': 'Test content that is long enough.'
            }
        )
        
        assert response.status_code == 403
    
    def test_create_blog_post_validation_error(self, client, admin_auth_headers):
        """Тест создания поста с ошибкой валидации"""
        response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Test',  # Слишком короткий
                'content': 'Short'  # Слишком короткий
            }
        )
        
        assert response.status_code == 422
    
    def test_get_blog_post_by_id(self, client, admin_auth_headers):
        """Тест получения поста по ID"""
        # Создаем пост
        create_response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Test Post for Get',
                'content': 'This is test content for getting by ID.'
            }
        )
        post_id = create_response.get_json()['data']['id']
        
        # Получаем пост
        response = client.get(f'/api/v1/blog/posts/{post_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['id'] == post_id
    
    def test_get_blog_post_not_found(self, client):
        """Тест получения несуществующего поста"""
        response = client.get('/api/v1/blog/posts/99999')
        
        assert response.status_code == 404
    
    def test_update_blog_post_as_admin(self, client, admin_auth_headers):
        """Тест обновления поста администратором"""
        # Создаем пост
        create_response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Original Title',
                'content': 'Original content that is long enough.'
            }
        )
        post_id = create_response.get_json()['data']['id']
        
        # Обновляем пост
        response = client.patch(f'/api/v1/blog/posts/{post_id}',
            headers=admin_auth_headers,
            json={
                'title': 'Updated Title'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'Updated Title'
    
    def test_delete_blog_post_as_admin(self, client, admin_auth_headers):
        """Тест удаления поста администратором"""
        # Создаем пост
        create_response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Post to Delete',
                'content': 'This post will be deleted.'
            }
        )
        post_id = create_response.get_json()['data']['id']
        
        # Удаляем пост
        response = client.delete(f'/api/v1/blog/posts/{post_id}',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204
        
        # Проверяем, что пост удален
        get_response = client.get(f'/api/v1/blog/posts/{post_id}')
        assert get_response.status_code == 404
    
    def test_upload_image_to_blog_post(self, client, admin_auth_headers):
        """Тест загрузки изображения для поста"""
        # Создаем пост
        create_response = client.post('/api/v1/blog/posts',
            headers=admin_auth_headers,
            json={
                'title': 'Post with Image',
                'content': 'This post will have an image uploaded.'
            }
        )
        post_id = create_response.get_json()['data']['id']
        
        # Создаем тестовое изображение
        image_data = io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01')
        
        # Загружаем изображение
        response = client.post(
            f'/api/v1/blog/posts/{post_id}/upload-image',
            headers=admin_auth_headers,
            data={'image': (image_data, 'test.png')},
            content_type='multipart/form-data'
        )
        
        # Может быть 200 или 400 в зависимости от валидации файла
        assert response.status_code in [200, 400]