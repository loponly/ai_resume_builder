"""Tests for the main AI Resume Builder application."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
import tempfile
import os
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import AIResumeBuilder


class TestAIResumeBuilder:
    """Test cases for the AIResumeBuilder class."""
    
    @pytest.fixture
    def app(self):
        """Create an AIResumeBuilder instance for testing."""
        return AIResumeBuilder()
    
    @pytest.fixture
    def sample_cv(self):
        """Sample CV content for testing."""
        return """
        John Doe
        Software Engineer
        Email: john.doe@email.com
        Phone: (555) 123-4567
        
        EXPERIENCE:
        Senior Developer at TechCorp (2020-2023)
        - Developed web applications using Python and JavaScript
        - Led team of 5 developers
        """
    
    @pytest.fixture
    def sample_job_description(self):
        """Sample job description for testing."""
        return """
        Senior Full Stack Developer
        TechFlow AI
        
        Requirements:
        - 5+ years of software development experience
        - Python, JavaScript, React experience
        - Experience with cloud platforms (AWS, GCP)
        - Strong leadership skills
        """
    
    def test_initialization(self, app):
        """Test that the application initializes correctly."""
        assert app is not None
        assert hasattr(app, 'coordinator')
        assert app.coordinator is not None
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    async def test_process_simple_direct_success(self, mock_model_class, mock_configure, app, sample_cv, sample_job_description):
        """Test successful direct LLM processing."""
        # Mock the LLM response
        mock_response = Mock()
        mock_response.text = """
        ## TAILORED RESUME:
        Optimized resume content here...
        
        ## COVER LETTER:
        Personalized cover letter here...
        
        ## QUALITY REVIEW:
        Quality feedback here...
        """
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Set environment variable
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-api-key'}):
            result = await app.process_simple_direct(
                cv_content=sample_cv,
                job_description=sample_job_description,
                user_id="test_user",
                user_name="Test User"
            )
        
        # Verify the result
        assert result["success"] is True
        assert result["user_id"] == "test_user"
        assert result["user_name"] == "Test User"
        assert len(result["generated_components"]) == 3
        assert "tailored_resume" in result["generated_components"]
        assert "cover_letter" in result["generated_components"]
        assert "quality_review" in result["generated_components"]
        
        # Verify LLM was called correctly
        mock_configure.assert_called_once_with(api_key='fake-api-key')
        mock_model_class.assert_called_once_with('gemini-1.5-flash')
        mock_model.generate_content.assert_called_once()
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    async def test_process_simple_direct_partial_response(self, mock_model_class, mock_configure, app, sample_cv, sample_job_description):
        """Test processing with partial LLM response (missing some sections)."""
        mock_response = Mock()
        mock_response.text = """
        ## TAILORED RESUME:
        Only resume content here...
        """
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-api-key'}):
            result = await app.process_simple_direct(
                cv_content=sample_cv,
                job_description=sample_job_description,
                user_id="test_user",
                user_name="Test User"
            )
        
        assert result["success"] is True
        assert len(result["generated_components"]) == 1
        assert "tailored_resume" in result["generated_components"]
        assert "cover_letter" not in result["generated_components"]
        assert "quality_review" not in result["generated_components"]
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    async def test_process_simple_direct_api_error(self, mock_model_class, mock_configure, app, sample_cv, sample_job_description):
        """Test handling of API errors during processing."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-api-key'}):
            result = await app.process_simple_direct(
                cv_content=sample_cv,
                job_description=sample_job_description,
                user_id="test_user",
                user_name="Test User"
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]
        assert result["user_id"] == "test_user"
    
    async def test_process_simple_direct_missing_api_key(self, app, sample_cv, sample_job_description):
        """Test handling of missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = await app.process_simple_direct(
                cv_content=sample_cv,
                job_description=sample_job_description,
                user_id="test_user",
                user_name="Test User"
            )
        
        assert result["success"] is False
        assert "error" in result
    
    def test_process_runner_result_complete(self, app):
        """Test processing a complete LLM response."""
        final_content = """
        ## TAILORED RESUME:
        Resume content...
        
        ## COVER LETTER:
        Cover letter content...
        
        ## QUALITY REVIEW:
        Quality review content...
        """
        
        result = app._process_runner_result(final_content, "test_user", "Test User")
        
        assert result["success"] is True
        assert result["user_id"] == "test_user"
        assert result["user_name"] == "Test User"
        assert len(result["generated_components"]) == 3
        assert "tailored_resume" in result["generated_components"]
        assert "cover_letter" in result["generated_components"]
        assert "quality_review" in result["generated_components"]
        assert result["final_content"] == final_content
    
    def test_process_runner_result_empty(self, app):
        """Test processing an empty LLM response."""
        final_content = ""
        
        result = app._process_runner_result(final_content, "test_user", "Test User")
        
        assert result["success"] is True
        assert result["user_id"] == "test_user"
        assert result["user_name"] == "Test User"
        assert len(result["generated_components"]) == 0
        assert result["final_content"] == final_content
    
    def test_save_results_success(self, app):
        """Test successful saving of results."""
        results = {
            "success": True,
            "user_id": "test_user",
            "session_id": "test_session",
            "generated_components": ["tailored_resume", "cover_letter"],
            "documents": {
                "tailored_resume": "Resume content...",
                "cover_letter": "Cover letter content..."
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = app.save_results(results, temp_dir)
            
            assert "results_json" in file_paths
            assert "tailored_resume" in file_paths
            assert "cover_letter" in file_paths
            
            # Verify files exist
            assert Path(file_paths["results_json"]).exists()
            assert Path(file_paths["tailored_resume"]).exists()
            assert Path(file_paths["cover_letter"]).exists()
    
    def test_save_results_minimal(self, app):
        """Test saving results with minimal data."""
        results = {
            "success": True,
            "user_id": "test_user"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = app.save_results(results, temp_dir)
            
            assert "results_json" in file_paths
            assert Path(file_paths["results_json"]).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
