#!/usr/bin/env python3
"""
AI Resume Builder - Main Application

An intelligent, multi-agent system that creates personalized, professional resumes 
and cover letters tailored to specific job opportunities.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime
from dotenv import load_dotenv

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

# Import ADK components
from google.adk.runners import InMemoryRunner
from google.genai import types

# Import our custom agents
from agents.core.simple_coordinator import SimpleResumeBuilderCoordinator
from agents.core.cv_analyzer import CVAnalyzer
from agents.core.job_parser import JobDescriptionParser
from agents.core.resume_tailor import ResumeTailor
from agents.core.cover_letter_gen import CoverLetterGenerator
from agents.core.quality_reviewer import QualityReviewer
from agents.data.database_manager import DatabaseManager
from agents.workflows.sequential_agent import ResumeBuilderSequentialAgent
from agents.workflows.parallel_agent import ResumeBuilderParallelAgent


class AIResumeBuilder:
    """
    Main AI Resume Builder application class.
    
    This class orchestrates the entire resume building process using a
    multi-agent system with specialized agents for different tasks.
    """
    
    def __init__(self):
        """Initialize the AI Resume Builder."""
        self.coordinator = None
        self.runner = None
        self._initialize_agents()
        self._initialize_runner()
    
    def _initialize_runner(self):
        """Initialize the ADK Runner with our coordinator agent."""
        self.runner = InMemoryRunner(
            agent=self.coordinator,
            app_name="AI Resume Builder"
        )
    
    def _initialize_agents(self) -> None:
        """Initialize all the specialized agents and workflows."""
        
        # Create individual specialized agents
        cv_analyzer = CVAnalyzer()
        job_parser = JobDescriptionParser()
        resume_tailor = ResumeTailor()
        cover_letter_gen = CoverLetterGenerator()
        quality_reviewer = QualityReviewer(quality_threshold=0.85)
        database_manager = DatabaseManager()
        
        # Create workflow agents
        # Parallel analysis of CV and job description
        analysis_workflow = ResumeBuilderParallelAgent(
            name="AnalysisWorkflow",
            sub_agents=[cv_analyzer, job_parser],
            description="Parallel analysis of CV and job description"
        )
        
        # Sequential content generation
        generation_workflow = ResumeBuilderSequentialAgent(
            name="GenerationWorkflow", 
            sub_agents=[resume_tailor, cover_letter_gen],
            description="Sequential generation of tailored resume and cover letter"
        )
        
        # Quality assurance and storage
        qa_workflow = ResumeBuilderSequentialAgent(
            name="QAWorkflow",
            sub_agents=[quality_reviewer, database_manager],
            description="Quality assurance and database storage"
        )
        
        # Main pipeline workflow
        main_pipeline = ResumeBuilderSequentialAgent(
            name="MainPipeline",
            sub_agents=[analysis_workflow, generation_workflow, qa_workflow],
            description="Main resume building pipeline"
        )
        
        # Create the main coordinator (simplified version)
        self.coordinator = SimpleResumeBuilderCoordinator(
            description="Simple coordinator for the AI Resume Builder system"
        )
    
    async def process_resume_request(
        self, 
        cv_content: str, 
        job_description: str,
        user_id: str = "anonymous",
        user_name: str = "User"
    ) -> Dict[str, Any]:
        """
        Process a resume building request using ADK Runner.
        
        Args:
            cv_content: The CV/resume content text
            job_description: The job description text
            user_id: User identifier
            user_name: User's name
            
        Returns:
            Dictionary containing the processing results
        """
        try:
            # Create user message with the input data
            user_message = types.Content(
                parts=[
                    types.Part(
                        text=f"""
                        Please help me create a tailored resume and cover letter for the following job opportunity.
                        
                        **My CV/Resume:**
                        {cv_content}
                        
                        **Job Description:**
                        {job_description}
                        
                        **User Information:**
                        - User ID: {user_id}
                        - Name: {user_name}
                        
                        Please analyze my CV, understand the job requirements, create a tailored resume, 
                        generate a cover letter, and provide quality feedback.
                        """
                    )
                ]
            )
            
            # Log the start of processing
            print(f"🚀 Starting resume building process for user: {user_name} ({user_id})")
            print(f"📄 CV length: {len(cv_content)} characters")
            print(f"💼 Job description length: {len(job_description)} characters")
            print(f"🔍 Message preview: {user_message.parts[0].text[:300]}...")
            print("-" * 60)
            
            # Create a session using the runner's session service
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            await self.runner.session_service.create_session(
                session_id=session_id,
                user_id=user_id,
                app_name="AI Resume Builder"
            )
            
            # Run the coordinator through the ADK Runner
            events = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            )
            
            # Process the events and get the final result
            final_response = ""
            event_count = 0
            async for event in events:
                event_count += 1
                print(f"🔍 Event {event_count}: {type(event).__name__}")
                
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    print(f"🎯 Final response event detected")
                    if hasattr(event, 'content') and event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                        print(f"📝 Final response length: {len(final_response)} characters")
                        break
                elif hasattr(event, 'content') and event.content and event.content.parts:
                    # Collect all content parts
                    final_response = event.content.parts[0].text
                    print(f"📝 Content received: {len(final_response)} characters")
                    
            print(f"🔍 Total events processed: {event_count}")
            print(f"📝 Final response preview: {final_response[:200]}..." if final_response else "❌ No final response received")
            
            # Process the result
            summary = self._process_runner_result(final_response, user_id, user_name)
            
            print("-" * 60)
            print("✅ Processing completed!")
            print(f"📊 Generated {len(summary.get('generated_components', []))} components")
            
            return summary
            
        except Exception as e:
            error_msg = f"Error processing resume request: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "user_id": user_id
            }
    
    async def process_simple_direct(self, cv_content: str, job_description: str, user_id: str, user_name: str) -> Dict[str, Any]:
        """
        Process resume request using direct LLM invocation (bypassing ADK runner).
        
        Args:
            cv_content: The CV/resume content
            job_description: The job description
            user_id: User identifier
            user_name: User's name
            
        Returns:
            Dictionary containing the processing results
        """
        try:
            # Create a simple prompt
            prompt = f"""
            Please help me create a tailored resume and cover letter for the following job opportunity.
            
            **My CV/Resume:**
            {cv_content}
            
            **Job Description:**
            {job_description}
            
            **User Information:**
            - User ID: {user_id}
            - Name: {user_name}
            
            Please analyze my CV, understand the job requirements, create a tailored resume, 
            generate a cover letter, and provide quality feedback.
            
            Please structure your response with clear sections:
            
            ## TAILORED RESUME:
            [Provide the optimized resume content here]
            
            ## COVER LETTER:
            [Provide the personalized cover letter here]
            
            ## QUALITY REVIEW:
            [Provide feedback and recommendations]
            """
            
            # Log the start of processing
            print(f"🚀 Starting direct LLM processing for user: {user_name} ({user_id})")
            print(f"📄 CV length: {len(cv_content)} characters")
            print(f"💼 Job description length: {len(job_description)} characters")
            print(f"🔍 Prompt length: {len(prompt)} characters")
            print("-" * 60)
            
            # Try to call the LLM directly using the Google Generative AI API
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            
            # Create the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Generate response
            print("🤖 Calling LLM directly...")
            response = model.generate_content(prompt)
            
            final_response = response.text
            print(f"📝 LLM response length: {len(final_response)} characters")
            print(f"📝 Response preview: {final_response[:300]}...")
            
            # Process the result
            summary = self._process_runner_result(final_response, user_id, user_name)
            
            print("-" * 60)
            print("✅ Direct processing completed!")
            print(f"📊 Generated {len(summary.get('generated_components', []))} components")
            
            return summary
            
        except Exception as e:
            error_msg = f"Error in direct processing: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "user_id": user_id
            }
    
    def _process_runner_result(self, final_content: str, user_id: str, user_name: str) -> Dict[str, Any]:
        """Process the result from the ADK Runner and extract components."""
        
        # Create summary
        summary = {
            "success": True,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
            "final_content": final_content,
            "generated_components": [],
            "documents": {},
            "processing_complete": True
        }
        
        # Extract structured components from the final content
        components = self._extract_components(final_content)
        
        if components["tailored_resume"]:
            summary["generated_components"].append("tailored_resume")
            summary["documents"]["tailored_resume"] = components["tailored_resume"]
            
        if components["cover_letter"]:
            summary["generated_components"].append("cover_letter")
            summary["documents"]["cover_letter"] = components["cover_letter"]
            
        if components["quality_review"]:
            summary["generated_components"].append("quality_review")
            summary["documents"]["quality_review"] = components["quality_review"]
        
        return summary
    
    def _extract_components(self, content: str) -> Dict[str, str]:
        """Extract individual components from the LLM response."""
        
        components = {
            "tailored_resume": "",
            "cover_letter": "",
            "quality_review": ""
        }
        
        # Split content by section headers
        sections = content.split("##")
        
        for section in sections:
            section = section.strip()
            if section.startswith("TAILORED RESUME:"):
                # Remove the header and get the content
                components["tailored_resume"] = section.replace("TAILORED RESUME:", "").strip()
            elif section.startswith("COVER LETTER:"):
                components["cover_letter"] = section.replace("COVER LETTER:", "").strip()
            elif section.startswith("QUALITY REVIEW:"):
                components["quality_review"] = section.replace("QUALITY REVIEW:", "").strip()
        
        return components
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "output") -> Dict[str, str]:
        """
        Save the results to markdown files.
        
        Args:
            results: The processing results
            output_dir: Directory to save results (default: "output")
            
        Returns:
            Dictionary with file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create a timestamp for unique file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = results.get("user_id", "user")
        file_paths = {}
        
        try:
            # Save full results as JSON for reference
            results_file = output_path / f"{timestamp}_{user_id}_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            file_paths["results_json"] = str(results_file)
            
            # Save individual documents as markdown files
            documents = results.get("documents", {})
            
            if "tailored_resume" in documents:
                resume_file = output_path / f"{timestamp}_{user_id}_tailored_resume.md"
                with open(resume_file, 'w') as f:
                    f.write("# Tailored Resume\n\n")
                    f.write(documents["tailored_resume"])
                file_paths["tailored_resume"] = str(resume_file)
            
            if "cover_letter" in documents:
                cover_letter_file = output_path / f"{timestamp}_{user_id}_cover_letter.md"
                with open(cover_letter_file, 'w') as f:
                    f.write("# Cover Letter\n\n")
                    f.write(documents["cover_letter"])
                file_paths["cover_letter"] = str(cover_letter_file)
            
            if "quality_review" in documents:
                quality_file = output_path / f"{timestamp}_{user_id}_quality_review.md"
                with open(quality_file, 'w') as f:
                    f.write("# Quality Review\n\n")
                    f.write(documents["quality_review"])
                file_paths["quality_review"] = str(quality_file)
            
            # Create a combined markdown file with all components
            if documents:
                combined_file = output_path / f"{timestamp}_{user_id}_complete_package.md"
                with open(combined_file, 'w') as f:
                    f.write("# Resume Package\n\n")
                    f.write(f"Generated on: {results.get('timestamp', 'N/A')}\n")
                    f.write(f"User: {results.get('user_name', 'N/A')}\n\n")
                    
                    if "tailored_resume" in documents:
                        f.write("## Tailored Resume\n\n")
                        f.write(documents["tailored_resume"])
                        f.write("\n\n---\n\n")
                    
                    if "cover_letter" in documents:
                        f.write("## Cover Letter\n\n")
                        f.write(documents["cover_letter"])
                        f.write("\n\n---\n\n")
                    
                    if "quality_review" in documents:
                        f.write("## Quality Review\n\n")
                        f.write(documents["quality_review"])
                        f.write("\n\n")
                
                file_paths["complete_package"] = str(combined_file)
            
            print(f"💾 Results saved to: {output_dir}")
            for doc_type, path in file_paths.items():
                print(f"   📄 {doc_type}: {path}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
        
        return file_paths


async def main():
    """Main function to run the AI Resume Builder."""
    
    print("🤖 AI Resume Builder")
    print("=" * 60)
    
    # Initialize the application
    app = AIResumeBuilder()
    
    # Check if sample files exist
    cv_file = Path("input/cvs/sample_cv.txt")
    job_file = Path("input/job_descriptions/sample_job.txt")
    
    if not cv_file.exists():
        print(f"❌ Sample CV file not found: {cv_file}")
        print("Please add a CV file to the input/cvs/ directory")
        return
    
    if not job_file.exists():
        print(f"❌ Sample job description file not found: {job_file}")
        print("Please add a job description file to the input/job_descriptions/ directory")
        return
    
    # Read input files
    try:
        with open(cv_file, 'r') as f:
            cv_content = f.read()
        
        with open(job_file, 'r') as f:
            job_description = f.read()
        
        print(f"📂 Loaded CV from: {cv_file}")
        print(f"📂 Loaded job description from: {job_file}")
        
    except Exception as e:
        print(f"❌ Error reading input files: {e}")
        return
    
    # Process the resume request using direct LLM call
    results = await app.process_simple_direct(
        cv_content=cv_content,
        job_description=job_description,
        user_id="demo_user",
        user_name="Demo User"
    )
    
    # Save results
    if results.get("success"):
        file_paths = app.save_results(results)
        
        print("\n" + "=" * 60)
        print("🎉 Resume building completed successfully!")
        print("\n📊 Summary:")
        print(f"   Generated Components: {len(results.get('generated_components', []))}")
        print(f"   Quality Score: {results.get('quality_score', 'N/A')}")
        print(f"   ATS Score: {results.get('ats_score', 'N/A')}")
        
        if "documents" in results:
            docs = results["documents"]
            if "tailored_resume" in docs:
                print(f"   📄 Tailored Resume: {len(docs['tailored_resume'])} characters")
            if "cover_letter" in docs:
                print(f"   📄 Cover Letter: {len(docs['cover_letter'])} characters")
    
    else:
        print(f"\n❌ Resume building failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
