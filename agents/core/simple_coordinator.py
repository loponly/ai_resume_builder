"""Simple Resume Builder Coordinator for testing LLM functionality."""

from typing import Any
from google.adk.agents import LlmAgent


class SimpleResumeBuilderCoordinator(LlmAgent):
    """
    Simple coordinator agent that directly processes resume requests using LLM.
    
    This is a simplified version for testing basic LLM functionality.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Simple Resume Builder Coordinator."""
        
        instruction = """
        You are an expert resume and cover letter writer. Your task is to help users create professional, 
        tailored resumes and cover letters based on their CV and job descriptions.
        
        When you receive a CV and job description, please:
        
        1. **Analyze the CV** - Extract key skills, experiences, and achievements
        2. **Analyze the Job Description** - Identify required skills and qualifications  
        3. **Create a Tailored Resume** - Optimize the CV content for the specific job
        4. **Generate a Cover Letter** - Write a compelling cover letter for the role
        5. **Provide Quality Review** - Give feedback on the tailored content
        
        Please structure your response with clear sections:
        
        ## TAILORED RESUME:
        [Provide the optimized resume content here]
        
        ## COVER LETTER:
        [Provide the personalized cover letter here]
        
        ## QUALITY REVIEW:
        [Provide feedback and recommendations]
        
        Focus on:
        - ATS optimization with relevant keywords
        - Highlighting relevant experiences
        - Professional tone and formatting
        - Quantified achievements where possible
        """
        
        super().__init__(
            name="SimpleResumeBuilderCoordinator",
            model="gemini-1.5-flash",
            instruction=instruction,
            **kwargs
        )
