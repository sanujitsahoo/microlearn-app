import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from main import (
    app, 
    generate_syllabus, 
    get_videos_for_module, 
    validate_and_sanitize_topic,
    validate_video_id
)

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


class TestValidateVideoId:
    """Tests for the validate_video_id function."""
    
    def test_validate_video_id_valid(self):
        """Test validation of valid YouTube video IDs."""
        assert validate_video_id("N20k-rV-iXQ") == True
        assert validate_video_id("G2fqAlgmoPo") == True
        assert validate_video_id("dQw4w9WgXcQ") == True
        assert validate_video_id("12345678901") == True  # 11 chars
        assert validate_video_id("abc_def-ghi") == True  # with special chars
    
    def test_validate_video_id_invalid(self):
        """Test validation of invalid YouTube video IDs."""
        assert validate_video_id("short") == False  # Too short
        assert validate_video_id("waytoolongvideoid12345") == False  # Too long
        assert validate_video_id("invalid@id") == False  # Invalid character
        assert validate_video_id("") == False  # Empty
        assert validate_video_id("1234567890") == False  # 10 chars (not 11)


class TestGetVideosForModule:
    """Tests for the get_videos_for_module function."""
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_success(self, mock_get):
        """Test successful video retrieval with valid video IDs."""
        # Mock YouTube API response with valid 11-character video IDs
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": {"videoId": "N20k-rV-iXQ"}},  # Valid 11-char ID
                {"id": {"videoId": "G2fqAlgmoPo"}},  # Valid 11-char ID
                {"id": {"videoId": "dQw4w9WgXcQ"}}   # Valid 11-char ID
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        assert len(result) == 3
        assert "N20k-rV-iXQ" in result
        assert "G2fqAlgmoPo" in result
        assert "dQw4w9WgXcQ" in result
        mock_get.assert_called_once()
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_filters_invalid_ids(self, mock_get):
        """Test that invalid video IDs are filtered out."""
        # Mock YouTube API response with mix of valid and invalid IDs
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": {"videoId": "N20k-rV-iXQ"}},  # Valid
                {"id": {"videoId": "invalid"}},      # Invalid (too short)
                {"id": {"videoId": "G2fqAlgmoPo"}}   # Valid
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should only return valid IDs
        assert len(result) == 2
        assert "N20k-rV-iXQ" in result
        assert "G2fqAlgmoPo" in result
        assert "invalid" not in result
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_empty_response(self, mock_get):
        """Test when YouTube API returns empty results."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_api_error(self, mock_get):
        """Test when YouTube API request fails."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
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
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"
    
    @patch('main.requests.get')
    @patch('main.YOUTUBE_API_KEY', 'test_key')
    def test_get_videos_http_error(self, mock_get):
        """Test when YouTube API returns HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        mock_get.return_value = mock_response
        
        result = get_videos_for_module("test search")
        
        # Should return fallback video
        assert len(result) == 1
        assert result[0] == "N20k-rV-iXQ"


class TestValidateAndSanitizeTopic:
    """Tests for the validate_and_sanitize_topic function."""
    
    def test_validate_topic_valid(self):
        """Test validation of valid topics."""
        assert validate_and_sanitize_topic("Python") == "Python"
        assert validate_and_sanitize_topic("Machine Learning") == "Machine Learning"
        assert validate_and_sanitize_topic("AI & ML") == "AI  ML"  # & removed
        assert validate_and_sanitize_topic("  JavaScript  ") == "JavaScript"  # Trims whitespace
    
    def test_validate_topic_empty(self):
        """Test validation rejects empty topics."""
        with pytest.raises(ValueError, match="non-empty"):
            validate_and_sanitize_topic("")
        with pytest.raises(ValueError, match="at least one valid character"):
            validate_and_sanitize_topic("   ")
    
    def test_validate_topic_too_long(self):
        """Test validation rejects topics that are too long."""
        long_topic = "a" * 201
        with pytest.raises(ValueError, match="200 characters"):
            validate_and_sanitize_topic(long_topic)
    
    def test_validate_topic_invalid_type(self):
        """Test validation rejects non-string types."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_and_sanitize_topic(None)
    
    def test_validate_topic_removes_dangerous_chars(self):
        """Test that dangerous characters are removed."""
        result = validate_and_sanitize_topic("Test<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result
        assert "/" not in result
        # Note: "script" as a word remains, but the dangerous chars <, >, / are removed
        # This is expected behavior - we sanitize special chars, not words


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
        mock_get_videos.side_effect = [["N20k-rV-iXQ", "G2fqAlgmoPo"], ["dQw4w9WgXcQ"]]
        
        response = client.get("/generate_course?topic=Test%20Topic")
        
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Test Topic"
        assert len(data["modules"]) == 2
        assert "videos" in data["modules"][0]
        assert data["modules"][0]["videos"] == ["N20k-rV-iXQ", "G2fqAlgmoPo"]
        assert data["modules"][1]["videos"] == ["dQw4w9WgXcQ"]
        # Should be called with sanitized topic
        mock_generate_syllabus.assert_called_once()
        assert mock_get_videos.call_count == 2
    
    @patch('main.generate_syllabus')
    def test_generate_course_ai_failure(self, mock_generate_syllabus):
        """Test when AI syllabus generation fails."""
        mock_generate_syllabus.return_value = None
        
        response = client.get("/generate_course?topic=Test%20Topic")
        
        assert response.status_code == 500
        # Updated error message
        assert "Unable to generate" in response.json()["detail"]
    
    def test_generate_course_empty_topic(self):
        """Test course generation with empty topic - should return 422 (FastAPI validation)."""
        response = client.get("/generate_course?topic=")
        
        # FastAPI Query validation happens first, returns 422 for empty required param
        # Our custom validation would return 400, but FastAPI catches it first
        assert response.status_code == 422
    
    def test_generate_course_topic_too_long(self):
        """Test course generation with topic that's too long."""
        long_topic = "a" * 201
        response = client.get(f"/generate_course?topic={long_topic}")
        
        # FastAPI Query validation with max_length=200 happens first, returns 422
        # Our custom validation would return 400, but FastAPI catches it first
        assert response.status_code == 422
    
    def test_generate_course_missing_topic(self):
        """Test course generation without topic parameter."""
        response = client.get("/generate_course")
        
        # Should return 422 Unprocessable Entity (FastAPI validation error)
        assert response.status_code == 422
    
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
        mock_get_videos.return_value = ["N20k-rV-iXQ", "G2fqAlgmoPo"]
        
        response = client.get("/generate_course?topic=Advanced%20Topic")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["modules"]) == 5
        assert mock_get_videos.call_count == 5
        # All modules should have videos
        for module in data["modules"]:
            assert "videos" in module
            assert len(module["videos"]) == 2
    
    @patch('main.generate_syllabus')
    def test_generate_course_unexpected_error(self, mock_generate_syllabus):
        """Test when an unexpected error occurs."""
        mock_generate_syllabus.side_effect = Exception("Unexpected error")
        
        response = client.get("/generate_course?topic=Test")
        
        assert response.status_code == 500
        # Should not expose internal error details
        assert "error occurred" in response.json()["detail"].lower()
        assert "Unexpected error" not in response.json()["detail"]


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

