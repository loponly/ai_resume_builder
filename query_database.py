#!/usr/bin/env python3
"""
Database Query Script - View stored data in the resume builder database
"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime

def query_database():
    """Query and display data from the resume builder database."""
    
    db_path = Path("data/database/resume_builder.db")
    
    if not db_path.exists():
        print("❌ Database file not found!")
        return
    
    print("🗄️  Resume Builder Database Contents")
    print("=" * 60)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query users
            print("\n👤 USERS:")
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"   ID: {user[0]}, User ID: {user[1]}, Name: {user[2]}")
            
            # Query processing sessions
            print("\n⚙️  PROCESSING SESSIONS:")
            cursor.execute("SELECT * FROM processing_sessions")
            sessions = cursor.fetchall()
            for session in sessions:
                print(f"   Session ID: {session[1]}")
                print(f"   User: {session[2]}, Status: {session[5]}")
                print(f"   Created: {session[6]}, Completed: {session[7]}")
                print()
            
            # Query tailored resumes
            print("\n📄 TAILORED RESUMES:")
            cursor.execute("SELECT session_id, LENGTH(resume_content), quality_score, created_at FROM tailored_resumes")
            resumes = cursor.fetchall()
            for resume in resumes:
                print(f"   Session: {resume[0]}")
                print(f"   Content Length: {resume[1]} characters")
                print(f"   Quality Score: {resume[2]}")
                print(f"   Created: {resume[3]}")
                print()
            
            # Query cover letters
            print("\n📝 COVER LETTERS:")
            cursor.execute("SELECT session_id, LENGTH(letter_content), quality_score, created_at FROM cover_letters")
            letters = cursor.fetchall()
            for letter in letters:
                print(f"   Session: {letter[0]}")
                print(f"   Content Length: {letter[1]} characters")
                print(f"   Quality Score: {letter[2]}")
                print(f"   Created: {letter[3]}")
                print()
            
            # Query original CVs
            print("\n📋 ORIGINAL CVs:")
            cursor.execute("SELECT user_id, LENGTH(cv_content), file_name, created_at FROM original_cvs")
            cvs = cursor.fetchall()
            for cv in cvs:
                print(f"   User: {cv[0]}")
                print(f"   Content Length: {cv[1]} characters")
                print(f"   File Name: {cv[2]}")
                print(f"   Created: {cv[3]}")
                print()
            
            # Query job descriptions
            print("\n💼 JOB DESCRIPTIONS:")
            cursor.execute("SELECT job_title, company_name, LENGTH(job_content), created_at FROM job_descriptions")
            jobs = cursor.fetchall()
            for job in jobs:
                print(f"   Title: {job[0]}")
                print(f"   Company: {job[1]}")
                print(f"   Content Length: {job[2]} characters")
                print(f"   Created: {job[3]}")
                print()
            
            # Get table counts
            print("\n📊 DATABASE STATISTICS:")
            tables = ['users', 'processing_sessions', 'tailored_resumes', 'cover_letters', 'original_cvs', 'job_descriptions']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} records")
    
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    query_database()
