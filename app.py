#!/usr/bin/env python3
"""
AI Resume Builder - Main Application

An intelligent system that creates personalized, professional resumes 
and cover letters for specific job opportunities.
"""
import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

# Load environment variables
load_dotenv()

# Debug environment variables
print(f"🔧 GEMINI_API_KEY set: {'GEMINI_API_KEY' in os.environ}")
print(f"🔧 GOOGLE_API_KEY set: {'GOOGLE_API_KEY' in os.environ}")
if 'GEMINI_API_KEY' in os.environ:
    print(f"🔧 GEMINI_API_KEY: {os.environ['GEMINI_API_KEY'][:10]}...")

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class AIResumeBuilder:
    """
    Main AI Resume Builder application class.
    
    This class reads all CVs and job descriptions, then generates
    one optimized resume and cover letter in both MD and PDF formats.
    """
    
    def __init__(self):
        """Initialize the AI Resume Builder."""
        self.input_dir = Path("input")
        self.cv_dir = self.input_dir / "cvs"
        self.job_dir = self.input_dir / "job_descriptions"
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure the Google Generative AI API
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def read_all_cvs(self) -> List[Dict[str, str]]:
        """Read all CV files from the input directory."""
        cvs = []
        cv_files = list(self.cv_dir.glob("*.txt"))
        
        for cv_file in cv_files:
            try:
                with open(cv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                cvs.append({
                    "filename": cv_file.name,
                    "content": content
                })
                print(f"📄 Loaded CV: {cv_file.name}")
            except Exception as e:
                print(f"❌ Error reading CV file {cv_file}: {e}")
        
        return cvs
    
    def read_all_job_descriptions(self) -> List[Dict[str, str]]:
        """Read all job description files from the input directory."""
        jobs = []
        job_files = list(self.job_dir.glob("*.txt"))
        
        for job_file in job_files:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                jobs.append({
                    "filename": job_file.name,
                    "content": content
                })
                print(f"💼 Loaded job description: {job_file.name}")
            except Exception as e:
                print(f"❌ Error reading job file {job_file}: {e}")
        
        return jobs
    
    async def generate_resume_and_cover_letter(
        self, 
        cvs: List[Dict[str, str]], 
        jobs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate optimized resume and cover letter based on all CVs and job descriptions.
        
        Args:
            cvs: List of CV data
            jobs: List of job description data
            
        Returns:
            Dictionary containing the generated content
        """
        try:
            # Combine all CV content
            combined_cv_content = "\n\n".join([cv["content"] for cv in cvs])
            
            # Combine all job descriptions
            combined_job_content = "\n\n".join([
                f"=== {job['filename']} ===\n{job['content']}" 
                for job in jobs
            ])
            
            # Create a comprehensive prompt
            prompt = f"""
            You are a professional resume writer and career consultant. Based on the provided CV(s) and job description(s), create one optimized professional resume and one compelling cover letter.

            **IMPORTANT GUIDELINES:**
            - Do NOT use words like "tailor", "tailored", "customized", "personalized" or similar terms in the output
            - Create a clean, professional resume that highlights the most relevant experience
            - Focus on achievements, metrics, and impact
            - Use action verbs and quantifiable results
            - Make the content flow naturally without mentioning adaptation or customization

            **CV CONTENT:**
            {combined_cv_content}

            **JOB OPPORTUNITIES:**
            {combined_job_content}

            Please provide your response in the following structured format:

            ## PROFESSIONAL RESUME

            [Provide a clean, professional resume that showcases the candidate's experience and skills most relevant to the job opportunities. Include all standard sections: contact info, professional summary, technical skills, professional experience with bullet points highlighting achievements, education, certifications, and projects. Make it ATS-friendly and well-formatted.]

            ## COVER LETTER

            [Provide a compelling cover letter that demonstrates enthusiasm for the opportunities and explains how the candidate's background makes them an ideal fit. Keep it concise, engaging, and professional. Address it generically to "Hiring Manager" since there are multiple potential positions.]

            ## FORMATTING NOTES

            [Provide brief notes about the resume structure and key highlights for optimal presentation]
            """
            
            print("🤖 Generating optimized resume and cover letter...")
            print(f"📊 Processing {len(cvs)} CV(s) and {len(jobs)} job description(s)")
            
            # Generate response
            response = self.model.generate_content(prompt)
            content = response.text
            
            print(f"✅ Generated content ({len(content)} characters)")
            
            # Extract sections
            sections = self._extract_sections(content)
            
            return {
                "success": True,
                "resume": sections.get("resume", ""),
                "cover_letter": sections.get("cover_letter", ""),
                "formatting_notes": sections.get("formatting_notes", ""),
                "timestamp": datetime.now().isoformat(),
                "cv_count": len(cvs),
                "job_count": len(jobs)
            }
            
        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from the generated content."""
        sections = {
            "resume": "",
            "cover_letter": "",
            "formatting_notes": ""
        }
        
        # Split by section headers
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith("## PROFESSIONAL RESUME"):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = "resume"
                current_content = []
            elif line_stripped.startswith("## COVER LETTER"):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = "cover_letter"
                current_content = []
            elif line_stripped.startswith("## FORMATTING NOTES"):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = "formatting_notes"
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def save_markdown_files(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Save resume and cover letter as markdown files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_paths = {}
        
        try:
            if data.get("resume"):
                resume_file = self.output_dir / f"{timestamp}_resume.md"
                with open(resume_file, 'w', encoding='utf-8') as f:
                    f.write(data["resume"])
                file_paths["resume_md"] = str(resume_file)
                print(f"💾 Saved resume: {resume_file}")
            
            if data.get("cover_letter"):
                cover_letter_file = self.output_dir / f"{timestamp}_cover_letter.md"
                with open(cover_letter_file, 'w', encoding='utf-8') as f:
                    f.write(data["cover_letter"])
                file_paths["cover_letter_md"] = str(cover_letter_file)
                print(f"💾 Saved cover letter: {cover_letter_file}")
            
        except Exception as e:
            print(f"❌ Error saving markdown files: {e}")
        
        return file_paths
    
    def _clean_text_for_pdf(self, text: str) -> str:
        """Clean text for PDF generation by removing markdown formatting."""
        # Remove markdown headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove markdown links but keep the text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def save_pdf_files(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Save resume and cover letter as PDF files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_paths = {}
        
        try:
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=6,
                spaceBefore=12
            )
            normal_style = styles['Normal']
            
            # Save resume as PDF
            if data.get("resume"):
                resume_pdf = self.output_dir / f"{timestamp}_resume.pdf"
                doc = SimpleDocTemplate(str(resume_pdf), pagesize=letter,
                                      rightMargin=72, leftMargin=72,
                                      topMargin=72, bottomMargin=18)
                
                story = []
                resume_text = self._clean_text_for_pdf(data["resume"])
                
                # Split into paragraphs and process
                paragraphs = resume_text.split('\n\n')
                
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    
                    # Check if it's a section header (all caps or starts with certain patterns)
                    if (para.isupper() and len(para) < 50) or \
                       any(para.startswith(prefix) for prefix in ['PROFESSIONAL SUMMARY', 'TECHNICAL SKILLS', 'PROFESSIONAL EXPERIENCE', 'EDUCATION', 'CERTIFICATIONS', 'PROJECTS', 'LANGUAGES']):
                        story.append(Paragraph(para, heading_style))
                    else:
                        # Handle bullet points
                        lines = para.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('•') or line.startswith('-'):
                                story.append(Paragraph(line, normal_style))
                            elif line:
                                story.append(Paragraph(line, normal_style))
                    
                    story.append(Spacer(1, 6))
                
                doc.build(story)
                file_paths["resume_pdf"] = str(resume_pdf)
                print(f"📄 Saved resume PDF: {resume_pdf}")
            
            # Save cover letter as PDF
            if data.get("cover_letter"):
                cover_letter_pdf = self.output_dir / f"{timestamp}_cover_letter.pdf"
                doc = SimpleDocTemplate(str(cover_letter_pdf), pagesize=letter,
                                      rightMargin=72, leftMargin=72,
                                      topMargin=72, bottomMargin=18)
                
                story = []
                cover_letter_text = self._clean_text_for_pdf(data["cover_letter"])
                
                # Add title
                story.append(Paragraph("Cover Letter", title_style))
                story.append(Spacer(1, 12))
                
                # Split into paragraphs
                paragraphs = cover_letter_text.split('\n\n')
                
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        story.append(Paragraph(para, normal_style))
                        story.append(Spacer(1, 12))
                
                doc.build(story)
                file_paths["cover_letter_pdf"] = str(cover_letter_pdf)
                print(f"📄 Saved cover letter PDF: {cover_letter_pdf}")
            
        except Exception as e:
            print(f"❌ Error saving PDF files: {e}")
        
        return file_paths
    
    async def process_all_inputs(self) -> Dict[str, Any]:
        """
        Main processing function that reads all inputs and generates output.
        
        Returns:
            Dictionary containing processing results and file paths
        """
        print("🚀 Starting AI Resume Builder")
        print("=" * 60)
        
        # Read all CVs
        print("📂 Reading CV files...")
        cvs = self.read_all_cvs()
        if not cvs:
            return {
                "success": False,
                "error": "No CV files found in input/cvs directory"
            }
        
        # Read all job descriptions
        print("📂 Reading job description files...")
        jobs = self.read_all_job_descriptions()
        if not jobs:
            return {
                "success": False,
                "error": "No job description files found in input/job_descriptions directory"
            }
        
        print(f"📊 Found {len(cvs)} CV(s) and {len(jobs)} job description(s)")
        print("-" * 60)
        
        # Generate content
        result = await self.generate_resume_and_cover_letter(cvs, jobs)
        
        if not result.get("success"):
            return result
        
        # Save files
        print("\n💾 Saving output files...")
        md_paths = self.save_markdown_files(result)
        pdf_paths = self.save_pdf_files(result)
        
        # Combine file paths
        all_paths = {**md_paths, **pdf_paths}
        result["file_paths"] = all_paths
        
        print("\n" + "=" * 60)
        print("🎉 Processing completed successfully!")
        print(f"📊 Generated files:")
        for file_type, path in all_paths.items():
            print(f"   {file_type}: {Path(path).name}")
        
        return result


async def main():
    """Main function to run the AI Resume Builder."""
    app = AIResumeBuilder()
    result = await app.process_all_inputs()
    
    if result.get("success"):
        print(f"\n✅ Success! Generated {len(result.get('file_paths', {}))} files")
        
        # Print summary
        if result.get("resume"):
            print(f"📄 Resume length: {len(result['resume'])} characters")
        if result.get("cover_letter"):
            print(f"📝 Cover letter length: {len(result['cover_letter'])} characters")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
