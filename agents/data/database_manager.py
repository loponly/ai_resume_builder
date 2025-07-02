"""Database Manager agent for handling SQLite operations."""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, AsyncGenerator, List
from pathlib import Path
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.base_agent import ResumeBuilderBaseAgent


class DatabaseManager(ResumeBuilderBaseAgent):
    """
    Manages SQLite database operations for document storage and analytics.
    
    This agent handles persistent storage of CVs, job descriptions, tailored resumes,
    cover letters, user feedback, and performance metrics.
    """
    
    def __init__(self, db_path: str = "data/database/resume_builder.db", **kwargs: Any) -> None:
        """
        Initialize the Database Manager agent.
        
        Args:
            db_path: Path to the SQLite database file
        """
        super().__init__(
            name="DatabaseManager",
            description="Manages SQLite database operations for persistent storage",
            **kwargs
        )
        
        self._db_path = Path(db_path)
        self._connection = None
        self._initialized_db = False
    
    def _setup_resources(self) -> None:
        """Setup database and create tables if they don't exist."""
        # Ensure directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        self._initialized_db = True
    
    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables as per the schema in README
                self._create_tables(cursor)
                conn.commit()
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database: {e}")
    
    def _create_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create all required database tables."""
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Original CVs storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS original_cvs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                cv_content TEXT NOT NULL,
                cv_hash TEXT UNIQUE NOT NULL,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Job descriptions storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT,
                job_content TEXT NOT NULL,
                job_hash TEXT UNIQUE NOT NULL,
                requirements_extracted TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Processing sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                cv_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                status TEXT DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (cv_id) REFERENCES original_cvs(id),
                FOREIGN KEY (job_id) REFERENCES job_descriptions(id)
            )
        """)
        
        # Tailored resumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tailored_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                resume_content TEXT NOT NULL,
                resume_version INTEGER DEFAULT 1,
                tailoring_strategy TEXT,
                keywords_matched TEXT,
                ats_score REAL,
                quality_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id)
            )
        """)
        
        # Cover letters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cover_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                letter_content TEXT NOT NULL,
                letter_version INTEGER DEFAULT 1,
                tone_analysis TEXT,
                personalization_score REAL,
                quality_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id)
            )
        """)
        
        # User feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_id INTEGER NOT NULL,
                user_rating INTEGER CHECK(user_rating >= 1 AND user_rating <= 5),
                feedback_text TEXT,
                specific_issues TEXT,
                suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id)
            )
        """)
        
        # Performance metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE NOT NULL,
                total_sessions INTEGER DEFAULT 0,
                successful_sessions INTEGER DEFAULT 0,
                average_user_rating REAL,
                average_quality_score REAL,
                average_ats_score REAL,
                improvement_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute database operations based on context.
        
        Args:
            context: The invocation context containing operation details
            
        Yields:
            Event: Events with database operation results
        """
        try:
            if not self._initialized_db:
                self.initialize()
            
            # Get operation type from context
            operation = self._get_operation_from_context(context)
            
            if operation == "store_session":
                result = await self._store_processing_session(context)
            elif operation == "store_cv":
                result = await self._store_cv(context)
            elif operation == "store_job":
                result = await self._store_job_description(context)
            elif operation == "store_results":
                result = await self._store_results(context)
            elif operation == "get_history":
                result = await self._get_user_history(context)
            else:
                result = {"error": f"Unknown operation: {operation}"}
            
            yield Event(
                actions=EventActions(
                    state_delta={"database_result": result}
                )
            )
            
        except Exception as e:
            yield Event(
                actions=EventActions(
                    state_delta={"database_error": str(e)}
                )
            )
    
    def _get_operation_from_context(self, context: InvocationContext) -> str:
        """Determine the database operation from context."""
        if not context.session or not context.session.state:
            return "store_session"  # Default operation
        
        state = context.session.state
        
        # Check what operation is requested
        if "db_operation" in state:
            return state["db_operation"]
        
        # Infer operation from available data
        if "tailored_resume" in state or "cover_letter" in state:
            return "store_results"
        elif "cv_content" in state:
            return "store_cv"
        elif "job_description" in state:
            return "store_job"
        else:
            return "store_session"
    
    async def _store_processing_session(self, context: InvocationContext) -> Dict[str, Any]:
        """Store a new processing session."""
        if not context.session or not context.session.state:
            return {"error": "No session data available"}
        
        state = context.session.state
        session_id = state.get("session_id", "unknown")
        user_id = state.get("user_id", "anonymous")
        
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure user exists
                cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
                    (user_id, state.get("user_name", "Unknown"))
                )
                
                # Store session (will be updated later with CV and job IDs)
                cursor.execute("""
                    INSERT OR REPLACE INTO processing_sessions 
                    (session_id, user_id, cv_id, job_id, status) 
                    VALUES (?, ?, 0, 0, 'initializing')
                """, (session_id, user_id))
                
                conn.commit()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "operation": "session_stored"
                }
                
        except Exception as e:
            return {"error": f"Failed to store session: {e}"}
    
    async def _store_cv(self, context: InvocationContext) -> Dict[str, Any]:
        """Store CV content."""
        if not context.session or not context.session.state:
            return {"error": "No session data available"}
        
        state = context.session.state
        cv_content = state.get("cv_content", "")
        user_id = state.get("user_id", "anonymous")
        
        if not cv_content:
            return {"error": "No CV content to store"}
        
        try:
            # Create hash for deduplication
            cv_hash = hashlib.md5(cv_content.encode()).hexdigest()
            
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Store CV
                cursor.execute("""
                    INSERT OR IGNORE INTO original_cvs 
                    (user_id, cv_content, cv_hash, file_name) 
                    VALUES (?, ?, ?, ?)
                """, (user_id, cv_content, cv_hash, state.get("cv_filename", "uploaded_cv.txt")))
                
                # Get CV ID
                cursor.execute("SELECT id FROM original_cvs WHERE cv_hash = ?", (cv_hash,))
                cv_id = cursor.fetchone()[0]
                
                conn.commit()
                
                return {
                    "success": True,
                    "cv_id": cv_id,
                    "cv_hash": cv_hash,
                    "operation": "cv_stored"
                }
                
        except Exception as e:
            return {"error": f"Failed to store CV: {e}"}
    
    async def _store_job_description(self, context: InvocationContext) -> Dict[str, Any]:
        """Store job description content."""
        if not context.session or not context.session.state:
            return {"error": "No session data available"}
        
        state = context.session.state
        job_content = state.get("job_description", "")
        job_requirements = state.get("job_requirements", {})
        
        if not job_content:
            return {"error": "No job description content to store"}
        
        try:
            # Create hash for deduplication
            job_hash = hashlib.md5(job_content.encode()).hexdigest()
            
            # Extract job details
            job_title = "Unknown Position"
            company_name = "Unknown Company"
            
            if isinstance(job_requirements, dict):
                job_title = job_requirements.get("job_title", job_title)
                company_info = job_requirements.get("company_info", {})
                if isinstance(company_info, dict):
                    company_name = company_info.get("company_name", company_name)
            
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Store job description
                cursor.execute("""
                    INSERT OR IGNORE INTO job_descriptions 
                    (job_title, company_name, job_content, job_hash, requirements_extracted, keywords) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job_title, 
                    company_name, 
                    job_content, 
                    job_hash,
                    json.dumps(job_requirements) if job_requirements else None,
                    json.dumps(job_requirements.get("keywords", [])) if job_requirements else None
                ))
                
                # Get job ID
                cursor.execute("SELECT id FROM job_descriptions WHERE job_hash = ?", (job_hash,))
                job_id = cursor.fetchone()[0]
                
                conn.commit()
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "job_hash": job_hash,
                    "job_title": job_title,
                    "operation": "job_stored"
                }
                
        except Exception as e:
            return {"error": f"Failed to store job description: {e}"}
    
    async def _store_results(self, context: InvocationContext) -> Dict[str, Any]:
        """Store tailored resume and cover letter results."""
        if not context.session or not context.session.state:
            return {"error": "No session data available"}
        
        state = context.session.state
        session_id = state.get("session_id", "unknown")
        
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                results = {"success": True, "stored": []}
                
                # Store tailored resume if available
                if "tailored_resume" in state:
                    cursor.execute("""
                        INSERT INTO tailored_resumes 
                        (session_id, resume_content, tailoring_strategy, keywords_matched, ats_score, quality_score) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        state["tailored_resume"],
                        json.dumps(state.get("skill_match_analysis", {})),
                        json.dumps(state.get("keywords_matched", [])),
                        state.get("ats_score"),
                        state.get("quality_score")
                    ))
                    results["stored"].append("tailored_resume")
                
                # Store cover letter if available
                if "cover_letter" in state:
                    cursor.execute("""
                        INSERT INTO cover_letters 
                        (session_id, letter_content, tone_analysis, personalization_score, quality_score) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        state["cover_letter"],
                        json.dumps(state.get("cover_letter_metadata", {})),
                        state.get("personalization_score"),
                        state.get("quality_score")
                    ))
                    results["stored"].append("cover_letter")
                
                # Update session status
                cursor.execute("""
                    UPDATE processing_sessions 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                    WHERE session_id = ?
                """, (session_id,))
                
                conn.commit()
                
                results["operation"] = "results_stored"
                return results
                
        except Exception as e:
            return {"error": f"Failed to store results: {e}"}
    
    async def _get_user_history(self, context: InvocationContext) -> Dict[str, Any]:
        """Get user's processing history."""
        if not context.session or not context.session.state:
            return {"error": "No session data available"}
        
        state = context.session.state
        user_id = state.get("user_id", "anonymous")
        
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent sessions
                cursor.execute("""
                    SELECT s.session_id, s.status, s.created_at, s.completed_at,
                           j.job_title, j.company_name
                    FROM processing_sessions s
                    JOIN job_descriptions j ON s.job_id = j.id
                    WHERE s.user_id = ?
                    ORDER BY s.created_at DESC
                    LIMIT 10
                """, (user_id,))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        "session_id": row[0],
                        "status": row[1],
                        "created_at": row[2],
                        "completed_at": row[3],
                        "job_title": row[4],
                        "company_name": row[5]
                    })
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "recent_sessions": sessions,
                    "total_sessions": len(sessions),
                    "operation": "history_retrieved"
                }
                
        except Exception as e:
            return {"error": f"Failed to get user history: {e}"}
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate MD5 hash of content for deduplication."""
        return hashlib.md5(content.encode()).hexdigest()
