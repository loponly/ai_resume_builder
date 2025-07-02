"""CV Analyzer agent for extracting and analyzing CV content."""

import json
from typing import Any, Dict, Optional, AsyncGenerator
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.llm_agent import ResumeBuilderLlmAgent


class CVAnalyzer(ResumeBuilderLlmAgent):
    """
    Analyzes applicant's CV to extract key information.
    
    This agent specializes in parsing CV text and extracting structured data
    including skills, experiences, achievements, and creating an applicant profile summary.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the CV Analyzer agent."""
        instruction = """
        You are a CV Analysis specialist. Your role is to analyze CV/resume content and extract structured information.
        
        **Primary Responsibilities:**
        1. Parse CV text and extract structured data
        2. Identify skills, experiences, and achievements
        3. Create comprehensive applicant profile summary
        4. Categorize information for optimal matching
        
        **Analysis Format:**
        Extract the following information in JSON format:
        - personal_info: Name, contact details, location
        - professional_summary: Brief professional overview
        - skills: Technical and soft skills categorized
        - work_experience: Detailed work history with achievements
        - education: Educational background
        - certifications: Professional certifications
        - achievements: Notable accomplishments
        - keywords: Important keywords for ATS optimization
        
        **Quality Standards:**
        - Ensure accuracy in data extraction
        - Maintain original context and meaning
        - Identify quantifiable achievements
        - Extract industry-specific terminology
        
        Store the analysis results in the session state under 'applicant_profile'.
        """
        
        super().__init__(
            name="CVAnalyzer",
            description="Analyzes CV content to extract structured applicant data",
            instruction=instruction,
            output_key="applicant_profile",
            **kwargs
        )
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute CV analysis logic.
        
        Args:
            context: The invocation context containing CV content
            
        Yields:
            Event: Events with analysis results
        """
        try:
            # Get CV content from session state or input
            cv_content = self._get_cv_content(context)
            
            if not cv_content:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No CV content found for analysis"}
                    )
                )
                return
            
            # Update instruction with specific CV content
            enhanced_instruction = f"""
            {self.instruction}
            
            **CV Content to Analyze:**
            {cv_content}
            
            Please analyze this CV and provide the structured information in JSON format.
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
                    state_delta={"cv_analysis_error": str(e)}
                )
            )
    
    def _get_cv_content(self, context: InvocationContext) -> Optional[str]:
        """
        Extract CV content from the context.
        
        Args:
            context: The invocation context
            
        Returns:
            CV content string or None if not found
        """
        if not context.session or not context.session.state:
            return None
        
        state = context.session.state
        
        # Try different possible keys for CV content
        cv_keys = ['cv_content', 'cv_text', 'resume_content', 'original_cv']
        
        for key in cv_keys:
            if key in state and state[key]:
                return str(state[key])
        
        return None
    
    def _validate_and_enhance_analysis(self, state_delta: Dict[str, Any]) -> None:
        """
        Validate and enhance the analysis results.
        
        Args:
            state_delta: The state delta containing analysis results
        """
        if 'applicant_profile' not in state_delta:
            return
        
        profile = state_delta['applicant_profile']
        
        # If profile is a string (JSON), try to parse it
        if isinstance(profile, str):
            try:
                profile = json.loads(profile)
                state_delta['applicant_profile'] = profile
            except json.JSONDecodeError:
                # If parsing fails, wrap in a structure
                state_delta['applicant_profile'] = {
                    'raw_analysis': profile,
                    'parsing_error': True
                }
                return
        
        # Ensure required fields exist
        required_fields = [
            'personal_info', 'professional_summary', 'skills', 
            'work_experience', 'education', 'keywords'
        ]
        
        for field in required_fields:
            if field not in profile:
                profile[field] = {}
        
        # Add metadata
        profile['analysis_metadata'] = {
            'agent': self.name,
            'analysis_completed': True,
            'total_sections': len([k for k, v in profile.items() if v and k != 'analysis_metadata'])
        }
        
        state_delta['applicant_profile'] = profile
