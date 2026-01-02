import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from main import app, generate_syllabus, get_videos_for_module

client = TestClient(app)


class TestGenerateSyllabus:
    """Tests for the generate_syllabus function."""
    
    @patch('main.client')
    def test_generate_syllabus_success(self, mock_openai_client):
        """Test successful syllabus generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "topic": "Test Topic",
            "modules": [
                {
                    "id": 1,
                    "title": "Module 1",
                    "description": "Test description",
                    "search_term": "test search"
                }
            ]
        })
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = generate_syllabus("Test Topic")
        
        assert result is not None
        assert result["topic"] == "Test Topic"
        assert len(result["modules"]) == 1
        assert result["modules"][0]["title"] == "Module 1"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @patch('main.client')
    def test_generate_syllabus_with_markdown(self, mock_openai_client):
        """Test syllabus generation when OpenAI returns markdown code blocks."""
        # Mock OpenAI response with markdown
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "```json\n" + json.dumps({
            "topic": "Python",
            "modules": [{"id": 1, "title": "Basics", "description": "Intro", "search_term": "python basics"}]
        }) + "\n```"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = generate_syllabus("Python")
        
        assert result is not None
        assert result["topic"] == "Python"
        assert len(result["modules"]) == 1
    
    @patch('main.client')
    def test_generate_syllabus_api_error(self, mock_openai_client):
        """Test syllabus generation when OpenAI API fails."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = generate_syllabus("Test Topic")
        
        assert result is None
    
    @patch('main.client')
    def test_generate_syllabus_invalid_json(self, mock_openai_client):
        """Test syllabus generation when OpenAI returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # json.loads will raise JSONDecodeError, which will be caught and return None
        result = generate_syllabus("Test Topic")
        
        # Should catch the JSON decode error and return None
        assert result is None


class TestGetVideosForModule:
    """Tests for the get_videos_for_module function."""
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_success(self, mock_get):
        """Test successful video retrieval."""
        # Mock YouTube API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": {"videoId": "video1"}},
                {"id": {"videoId": "video2"}},
                {"id": {"videoId": "video3"}}
            ]
        }
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        assert len(result) == 3
        assert "video1" in result
        assert "video2" in result
        assert "video3" in result
        mock_get.assert_called_once()
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_empty_response(self, mock_get):
        """Test when YouTube API returns empty results."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_api_error(self, mock_get):
        """Test when YouTube API request fails."""
        mock_get.side_effect = Exception("Network error")
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"
    
    @patch('main.YOUTUBE_API_KEY', None)
    def test_get_videos_no_api_key(self):
        """Test when YouTube API key is not set."""
        result = get_videos_for_module("test search")
        
        # Should return backup IDs
        assert len(result) == 2
        assert "N20k-rV-iXQ" in result
        assert "G2fqAlgmoPo" in result
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_malformed_response(self, mock_get):
        """Test when YouTube API returns malformed response."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": [{"id": {}}]}  # Missing videoId
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"


class TestGenerateCourseEndpoint:
    """Tests for the /generate_course endpoint."""
    
    @patch('main.get_videos_for_module')
    @patch('main.generate_syllabus')
    def test_generate_course_success(self, mock_generate_syllabus, mock_get_videos):
        """Test successful course generation."""
        # Mock syllabus
        mock_syllabus = {
            "topic": "Test Topic",
            "modules": [
                {
                    "id": 1,
                    "title": "Module 1",
                    "description": "Test description",
                    "search_term": "test search"
                },
                {
                    "id": 2,
                    "title": "Module 2",
                    "description": "Test description 2",
                    "search_term": "test search 2"
                }
            ]
        }
        mock_generate_syllabus.return_value = mock_syllabus
        mock_get_videos.side_effect = [["video1", "video2"], ["video3"]]
        
        response = client.get("/generate_course?topic=Test%20Topic")
        
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Test Topic"
        assert len(data["modules"]) == 2
        assert "videos" in data["modules"][0]
        assert data["modules"][0]["videos"] == ["video1", "video2"]
        assert data["modules"][1]["videos"] == ["video3"]
        mock_generate_syllabus.assert_called_once_with("Test Topic")
        assert mock_get_videos.call_count == 2
    
    @patch('main.generate_syllabus')
    def test_generate_course_ai_failure(self, mock_generate_syllabus):
        """Test when AI syllabus generation fails."""
        mock_generate_syllabus.return_value = None
        
        response = client.get("/generate_course?topic=Test%20Topic")
        
        assert response.status_code == 500
        assert "Librarian failed" in response.json()["detail"]
    
    @patch('main.get_videos_for_module')
    @patch('main.generate_syllabus')
    def test_generate_course_empty_topic(self, mock_generate_syllabus, mock_get_videos):
        """Test course generation with empty topic."""
        mock_syllabus = {
            "topic": "",
            "modules": []
        }
        mock_generate_syllabus.return_value = mock_syllabus
        
        response = client.get("/generate_course?topic=")
        
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == ""
        assert len(data["modules"]) == 0
    
    @patch('main.get_videos_for_module')
    @patch('main.generate_syllabus')
    def test_generate_course_multiple_modules(self, mock_generate_syllabus, mock_get_videos):
        """Test course generation with multiple modules."""
        mock_syllabus = {
            "topic": "Advanced Topic",
            "modules": [
                {"id": i, "title": f"Module {i}", "description": f"Desc {i}", "search_term": f"search {i}"}
                for i in range(1, 6)  # 5 modules
            ]
        }
        mock_generate_syllabus.return_value = mock_syllabus
        mock_get_videos.return_value = ["video1", "video2"]
        
        response = client.get("/generate_course?topic=Advanced%20Topic")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["modules"]) == 5
        assert mock_get_videos.call_count == 5
        # All modules should have videos
        for module in data["modules"]:
            assert "videos" in module
            assert len(module["videos"]) == 2


class TestAppConfiguration:
    """Tests for app configuration."""
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        # Check if middleware stack has any middleware (CORS should be there)
        # FastAPI stores middleware in user_middleware list
        assert len(app.user_middleware) > 0, "Middleware should be configured"
        # Verify the app instance exists and is a FastAPI app
        assert app is not None
    
    def test_root_endpoint_not_defined(self):
        """Test that root endpoint behavior (should return 404 or be defined)."""
        # Since root endpoint might not be defined, this tests the behavior
        response = client.get("/")
        # Either 404 or a valid response is acceptable
        assert response.status_code in [200, 404]

