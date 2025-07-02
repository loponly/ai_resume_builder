"""Integration tests for the AI Resume Builder."""

import pytest
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, Mock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import AIResumeBuilder


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def sample_files(self):
        """Create temporary sample files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary CV file
            cv_content = """
            John Doe
            Software Engineer
            Email: john.doe@email.com
            Phone: (555) 123-4567
            
            EXPERIENCE:
            Senior Developer at TechCorp (2020-2023)
            - Developed web applications using Python and JavaScript
            - Led team of 5 developers
            """
            
            job_content = """
            Senior Full Stack Developer
            TechFlow AI
            
            Requirements:
            - 5+ years of software development experience
            - Python, JavaScript, React experience
            - Experience with cloud platforms (AWS, GCP)
            - Strong leadership skills
            """
            
            cv_file = Path(temp_dir) / "test_cv.txt"
            job_file = Path(temp_dir) / "test_job.txt"
            
            cv_file.write_text(cv_content)
            job_file.write_text(job_content)
            
            yield {
                "cv_file": cv_file,
                "job_file": job_file,
                "cv_content": cv_content,
                "job_content": job_content
            }
    
    def test_application_initialization(self):
        """Test that the application initializes correctly."""
        app = AIResumeBuilder()
        
        # Check that required components are initialized
        assert app.coordinator is not None
        assert app.runner is not None
        assert hasattr(app, '_initialize_agents')
        assert hasattr(app, '_initialize_runner')
    
    @pytest.mark.asyncio
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    async def test_end_to_end_processing(self, mock_model_class, mock_configure, sample_files):
        """Test complete end-to-end processing pipeline."""
        # Mock the LLM response
        mock_response = Mock()
        mock_response.text = """
        ## TAILORED RESUME:
        **John Doe**
        Senior Software Engineer
        john.doe@email.com | (555) 123-4567
        
        **Professional Summary**
        Experienced Senior Software Engineer with 5+ years in full stack development...
        
        ## COVER LETTER:
        Dear Hiring Manager,
        
        I am writing to express my interest in the Senior Full Stack Developer position at TechFlow AI...
        
        ## QUALITY REVIEW:
        **Strengths:**
        - Strong alignment with job requirements
        - Quantified achievements included
        - Professional formatting
        
        **Recommendations:**
        - Add more specific cloud platform experience
        - Include relevant certifications
        """
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        app = AIResumeBuilder()
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-api-key'}):
            result = await app.process_simple_direct(
                cv_content=sample_files["cv_content"],
                job_description=sample_files["job_content"],
                user_id="integration_test_user",
                user_name="Integration Test User"
            )
        
        # Verify successful processing
        assert result["success"] is True
        assert result["user_id"] == "integration_test_user"
        assert result["user_name"] == "Integration Test User"
        assert len(result["generated_components"]) == 3
        assert "tailored_resume" in result["generated_components"]
        assert "cover_letter" in result["generated_components"]
        assert "quality_review" in result["generated_components"]
        
        # Verify response content structure
        assert "final_content" in result
        assert "## TAILORED RESUME:" in result["final_content"]
        assert "## COVER LETTER:" in result["final_content"]
        assert "## QUALITY REVIEW:" in result["final_content"]
    
    @pytest.mark.asyncio
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    async def test_file_saving_integration(self, mock_model_class, mock_configure, sample_files):
        """Test file saving integration."""
        # Mock the LLM response
        mock_response = Mock()
        mock_response.text = """
        ## TAILORED RESUME:
        Resume content here...
        
        ## COVER LETTER:
        Cover letter content here...
        
        ## QUALITY REVIEW:
        Quality review here...
        """
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        app = AIResumeBuilder()
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-api-key'}):
            result = await app.process_simple_direct(
                cv_content=sample_files["cv_content"],
                job_description=sample_files["job_content"],
                user_id="file_test_user",
                user_name="File Test User"
            )
        
        # Test file saving
        with tempfile.TemporaryDirectory() as temp_output:
            file_paths = app.save_results(result, temp_output)
            
            # Verify files were created
            assert "results_json" in file_paths
            assert Path(file_paths["results_json"]).exists()
            
            # Read and verify JSON content
            import json
            with open(file_paths["results_json"], 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["success"] is True
            assert saved_data["user_id"] == "file_test_user"
            assert len(saved_data["generated_components"]) == 3
    
    def test_real_files_exist(self):
        """Test that the actual input files exist and are readable."""
        cv_file = Path("input/cvs/sample_cv.txt")
        job_file = Path("input/job_descriptions/sample_job.txt")
        
        assert cv_file.exists(), f"Sample CV file not found: {cv_file}"
        assert job_file.exists(), f"Sample job description file not found: {job_file}"
        
        # Test reading the files
        cv_content = cv_file.read_text()
        job_content = job_file.read_text()
        
        assert len(cv_content) > 0
        assert len(job_content) > 0
        assert "Software Engineer" in cv_content
        assert "John Doe" in cv_content
    
    def test_output_directory_creation(self):
        """Test that output directories are created correctly."""
        app = AIResumeBuilder()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_results = {
                "success": True,
                "user_id": "test_user",
                "session_id": "test_session"
            }
            
            output_dir = Path(temp_dir) / "test_output"
            file_paths = app.save_results(test_results, str(output_dir))
            
            # Verify directory was created
            assert output_dir.exists()
            assert output_dir.is_dir()
            
            # Verify results file was created
            assert "results_json" in file_paths
            assert Path(file_paths["results_json"]).exists()


class TestEnvironmentConfiguration:
    """Test environment configuration and setup."""
    
    def test_environment_variables_loading(self):
        """Test that environment variables are loaded correctly."""
        # Test with mock environment
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key', 'GEMINI_API_KEY': 'test_gemini_key'}):
            # Reload the environment
            from dotenv import load_dotenv
            load_dotenv()
            
            assert 'GOOGLE_API_KEY' in os.environ
            assert 'GEMINI_API_KEY' in os.environ
    
    def test_project_structure(self):
        """Test that the project structure is correct."""
        project_root = Path(__file__).parent.parent
        
        # Test required directories exist
        required_dirs = [
            "agents",
            "agents/base",
            "agents/core", 
            "agents/workflows",
            "agents/data",
            "config",
            "input",
            "input/cvs",
            "input/job_descriptions",
            "tests"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Required directory not found: {dir_path}"
            assert full_path.is_dir(), f"Path is not a directory: {dir_path}"
        
        # Test required files exist
        required_files = [
            "app.py",
            "README.md",
            "requirements.txt",
            "agents/__init__.py",
            "agents/base/__init__.py",
            "agents/core/__init__.py",
            "agents/workflows/__init__.py",
            "agents/data/__init__.py"
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Required file not found: {file_path}"
            assert full_path.is_file(), f"Path is not a file: {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
