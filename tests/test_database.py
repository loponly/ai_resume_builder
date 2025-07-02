"""
Tests for database functionality in the AI Resume Builder.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import AIResumeBuilder


class TestDatabaseFunctionality:
    """Test database storage and retrieval functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = AIResumeBuilder()
    
    @patch('app.DatabaseManager')
    def test_database_storage_success(self, mock_db_manager):
        """Test successful database storage."""
        # Mock the database manager
        mock_instance = MagicMock()
        mock_db_manager.return_value = mock_instance
        
        # Mock results data
        results = {
            "success": True,
            "user_id": "test_user",
            "user_name": "Test User",
            "timestamp": "2023-01-01T12:00:00",
            "documents": {
                "tailored_resume": "Test resume content",
                "cover_letter": "Test cover letter content",
                "quality_review": "Test quality review content"
            },
            "original_cv_content": "Test CV content",
            "original_job_content": "Test job content"
        }
        
        # Mock database operations to succeed
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = [1]  # Mock CV/Job ID
            
            # Call the database storage method
            db_result = self.app._store_in_database(results, "20230101_120000")
            
            # Check results
            assert db_result["success"] is True
            assert "session_id" in db_result
            assert db_result["session_id"] == "session_20230101_120000_test_user"
            assert "tailored_resume" in db_result["stored_documents"]
            assert "cover_letter" in db_result["stored_documents"]
    
    @patch('app.DatabaseManager')
    def test_database_storage_without_content(self, mock_db_manager):
        """Test database storage without original content."""
        # Mock the database manager
        mock_instance = MagicMock()
        mock_db_manager.return_value = mock_instance
        
        results = {
            "success": True,
            "user_id": "test_user",
            "user_name": "Test User",
            "timestamp": "2023-01-01T12:00:00",
            "documents": {
                "tailored_resume": "Test resume content"
            }
            # No original_cv_content or original_job_content
        }
        
        # Mock database operations to succeed
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            db_result = self.app._store_in_database(results, "20230101_120000")
            
            # Should still succeed but with minimal data
            assert db_result["success"] is True
            assert "session_id" in db_result
            assert "tailored_resume" in db_result["stored_documents"]
    
    def test_database_storage_error_handling(self):
        """Test database storage error handling."""
        # Test with missing required fields
        results = {
            "documents": {},
            # Missing user_id and user_name
        }
        
        db_result = self.app._store_in_database(results, "20230101_120000")
        
        # Should handle errors gracefully
        assert db_result["success"] is False
        assert "error" in db_result
    
    def test_save_results_with_database(self):
        """Test save_results method includes database storage."""
        results = {
            "success": True,
            "user_id": "test_user",
            "user_name": "Test User",
            "timestamp": "2023-01-01T12:00:00",
            "documents": {
                "tailored_resume": "Test resume content",
                "cover_letter": "Test cover letter content"
            },
            "original_cv_content": "Test CV content",
            "original_job_content": "Test job content"
        }
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the _store_in_database method to avoid actual DB operations
            with patch.object(self.app, '_store_in_database') as mock_db_store:
                mock_db_store.return_value = {
                    "success": True,
                    "session_id": "test_session_123"
                }
                
                file_paths = self.app.save_results(results, temp_dir)
                
                # Check that database storage was called
                mock_db_store.assert_called_once()
                
                # Check that database storage info is included in file_paths
                assert "database_storage" in file_paths
                assert "Session ID: test_session_123" in file_paths["database_storage"]
    
    def test_database_query_functionality(self):
        """Test database can be queried successfully."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # Initialize database manager to create tables
            from agents.data.database_manager import DatabaseManager
            db_manager = DatabaseManager(db_path=db_path)
            db_manager._setup_resources()
            
            # Insert test data
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Insert test user
                cursor.execute("""
                    INSERT INTO users (user_id, name) VALUES (?, ?)
                """, ("test_user", "Test User"))
                
                # Insert test session
                cursor.execute("""
                    INSERT INTO processing_sessions 
                    (session_id, user_id, cv_id, job_id, status) 
                    VALUES (?, ?, ?, ?, ?)
                """, ("test_session", "test_user", 1, 1, "completed"))
                
                conn.commit()
            
            # Query the data back
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check user exists
                cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", ("test_user",))
                user_count = cursor.fetchone()[0]
                assert user_count == 1
                
                # Check session exists
                cursor.execute("SELECT COUNT(*) FROM processing_sessions WHERE session_id = ?", ("test_session",))
                session_count = cursor.fetchone()[0]
                assert session_count == 1
        
        finally:
            # Clean up
            os.unlink(db_path)


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    def test_end_to_end_with_database(self):
        """Test complete flow including database storage."""
        # This is more of a smoke test to ensure database integration doesn't break
        app = AIResumeBuilder()
        
        # Mock results that would come from LLM processing
        results = {
            "success": True,
            "user_id": "integration_test_user",
            "user_name": "Integration Test User",
            "timestamp": "2023-01-01T12:00:00",
            "documents": {
                "tailored_resume": "Integration test resume content",
                "cover_letter": "Integration test cover letter content",
                "quality_review": "Integration test quality review content"
            },
            "original_cv_content": "Integration test CV content",
            "original_job_content": "Integration test job content"
        }
        
        # Use temporary directory for file output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock database storage to avoid actual DB operations in tests
            with patch.object(app, '_store_in_database') as mock_db_store:
                mock_db_store.return_value = {
                    "success": True,
                    "session_id": "integration_test_session_123",
                    "stored_documents": ["tailored_resume", "cover_letter"]
                }
                
                # Call save_results
                file_paths = app.save_results(results, temp_dir)
                
                # Verify files were created
                assert "tailored_resume" in file_paths
                assert "cover_letter" in file_paths
                assert "quality_review" in file_paths
                assert "complete_package" in file_paths
                assert "database_storage" in file_paths
                
                # Verify actual files exist
                for key, path in file_paths.items():
                    if key != "database_storage":  # Skip database storage info
                        assert Path(path).exists(), f"File not found: {path}"
