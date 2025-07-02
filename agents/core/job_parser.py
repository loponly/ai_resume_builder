"""Job Description Parser agent for analyzing job requirements."""

import json
from typing import Any, Dict, Optional, AsyncGenerator
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.llm_agent import ResumeBuilderLlmAgent


class JobDescriptionParser(ResumeBuilderLlmAgent):
    """
    Analyzes job descriptions to understand requirements and extract key information.
    
    This agent specializes in parsing job descriptions and extracting structured data
    including requirements, qualifications, keywords, and company culture indicators.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Job Description Parser agent."""
        instruction = """
        You are a Job Description Analysis specialist. Your role is to analyze job postings and extract comprehensive requirement information.
        
        **Primary Responsibilities:**
        1. Extract key requirements and qualifications
        2. Identify important keywords and skills
        3. Determine company culture and values
        4. Analyze job level and experience requirements
        5. Extract salary and benefits information if available
        
        **Analysis Format:**
        Extract the following information in JSON format:
        - job_title: Official job title
        - company_info: Company name, industry, size if mentioned
        - job_summary: Brief overview of the role
        - required_skills: Must-have technical and soft skills
        - preferred_skills: Nice-to-have skills and qualifications
        - experience_requirements: Years of experience, level (junior/mid/senior)
        - education_requirements: Degree requirements, certifications
        - responsibilities: Key job responsibilities
        - company_culture: Values, work environment, culture indicators
        - keywords: Important keywords for ATS optimization
        - benefits: Salary range, benefits, perks if mentioned
        - location_requirements: Remote, on-site, hybrid information
        
        **Quality Standards:**
        - Distinguish between required vs. preferred qualifications
        - Identify industry-specific terminology
        - Extract quantifiable requirements (years of experience, etc.)
        - Capture company culture and values indicators
        
        Store the analysis results in the session state under 'job_requirements'.
        """
        
        super().__init__(
            name="JobDescriptionParser",
            description="Analyzes job descriptions to extract requirements and key information",
            instruction=instruction,
            output_key="job_requirements",
            **kwargs
        )
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute job description analysis logic.
        
        Args:
            context: The invocation context containing job description content
            
        Yields:
            Event: Events with analysis results
        """
        try:
            # Get job description content from session state or input
            job_content = self._get_job_content(context)
            
            if not job_content:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No job description content found for analysis"}
                    )
                )
                return
            
            # Update instruction with specific job content
            enhanced_instruction = f"""
            {self.instruction}
            
            **Job Description to Analyze:**
            {job_content}
            
            Please analyze this job description and provide the structured information in JSON format.
            Pay special attention to distinguishing between required and preferred qualifications.
            """
            
            # Update the agent's instruction temporarily
            original_instruction = self.instruction
            self.instruction = enhanced_instruction
            
            try:
                # Execute the LLM analysis
                async for event in super()._execute_agent_logic(context):
                    # Process and validate the response
                    if event.actions and event.actions.state_delta:
                        # Try to parse and validate the extracted data
                        self._validate_and_enhance_analysis(event.actions.state_delta)
                    yield event
            finally:
                # Restore original instruction
                self.instruction = original_instruction
                
        except Exception as e:
            yield Event(
                actions=EventActions(
                    state_delta={"job_analysis_error": str(e)}
                )
            )
    
    def _get_job_content(self, context: InvocationContext) -> Optional[str]:
        """
        Extract job description content from the context.
        
        Args:
            context: The invocation context
            
        Returns:
            Job description content string or None if not found
        """
        if not context.session or not context.session.state:
            return None
        
        state = context.session.state
        
        # Try different possible keys for job description content
        job_keys = ['job_description', 'job_content', 'jd_content', 'job_text']
        
        for key in job_keys:
            if key in state and state[key]:
                return str(state[key])
        
        return None
    
    def _validate_and_enhance_analysis(self, state_delta: Dict[str, Any]) -> None:
        """
        Validate and enhance the analysis results.
        
        Args:
            state_delta: The state delta containing analysis results
        """
        if 'job_requirements' not in state_delta:
            return
        
        requirements = state_delta['job_requirements']
        
        # If requirements is a string (JSON), try to parse it
        if isinstance(requirements, str):
            try:
                requirements = json.loads(requirements)
                state_delta['job_requirements'] = requirements
            except json.JSONDecodeError:
                # If parsing fails, wrap in a structure
                state_delta['job_requirements'] = {
                    'raw_analysis': requirements,
                    'parsing_error': True
                }
                return
        
        # Ensure required fields exist
        required_fields = [
            'job_title', 'company_info', 'job_summary', 'required_skills',
            'preferred_skills', 'experience_requirements', 'responsibilities', 'keywords'
        ]
        
        for field in required_fields:
            if field not in requirements:
                requirements[field] = {} if field in ['company_info', 'experience_requirements'] else []
        
        # Process and categorize skills
        self._categorize_skills(requirements)
        
        # Add metadata
        requirements['analysis_metadata'] = {
            'agent': self.name,
            'analysis_completed': True,
            'total_requirements': len(requirements.get('required_skills', [])),
            'total_preferred': len(requirements.get('preferred_skills', [])),
            'has_company_info': bool(requirements.get('company_info', {}))
        }
        
        state_delta['job_requirements'] = requirements
    
    def _categorize_skills(self, requirements: Dict[str, Any]) -> None:
        """
        Categorize skills into technical and soft skills.
        
        Args:
            requirements: The requirements dictionary to enhance
        """
        required_skills = requirements.get('required_skills', [])
        preferred_skills = requirements.get('preferred_skills', [])
        
        # Common technical skill indicators
        technical_indicators = [
            'programming', 'coding', 'development', 'software', 'python', 'java',
            'javascript', 'react', 'angular', 'vue', 'database', 'sql', 'aws',
            'azure', 'gcp', 'docker', 'kubernetes', 'api', 'framework', 'library'
        ]
        
        # Categorize required skills
        tech_skills = []
        soft_skills = []
        
        for skill in required_skills:
            skill_lower = str(skill).lower()
            if any(indicator in skill_lower for indicator in technical_indicators):
                tech_skills.append(skill)
            else:
                soft_skills.append(skill)
        
        requirements['categorized_skills'] = {
            'technical_required': tech_skills,
            'soft_required': soft_skills,
            'technical_preferred': [
                skill for skill in preferred_skills
                if any(indicator in str(skill).lower() for indicator in technical_indicators)
            ],
            'soft_preferred': [
                skill for skill in preferred_skills
                if not any(indicator in str(skill).lower() for indicator in technical_indicators)
            ]
        }
