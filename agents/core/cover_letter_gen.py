"""Cover Letter Generator agent for creating personalized cover letters."""

import json
from typing import Any, Dict, Optional, AsyncGenerator
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.llm_agent import ResumeBuilderLlmAgent


class CoverLetterGenerator(ResumeBuilderLlmAgent):
    """
    Creates personalized cover letters/proposal letters.
    
    This agent specializes in generating compelling cover letters that highlight
    relevant achievements, address specific job requirements, and create professional
    opening and closing statements.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Cover Letter Generator agent."""
        instruction = """
        You are a Cover Letter Writing specialist. Your role is to create compelling, personalized cover letters that maximize job application success.
        
        **Primary Responsibilities:**
        1. Generate compelling opening statements related to the specific company/role
        2. Highlight relevant achievements and experiences
        3. Address specific job requirements and demonstrate fit
        4. Create professional closing statements with clear call-to-action
        5. Adapt tone to company culture and industry standards
        
        **Cover Letter Structure:**
        1. **Header**: Professional contact information
        2. **Salutation**: Personalized greeting (research hiring manager if possible)
        3. **Opening Paragraph**: 
           - Hook that grabs attention
           - Mention specific role and company
           - Brief value proposition
        4. **Body Paragraphs** (1-2):
           - Specific examples of relevant achievements
           - Direct alignment with job requirements
           - Demonstrate knowledge of company/industry
           - Show enthusiasm and cultural fit
        5. **Closing Paragraph**:
           - Summarize key value proposition
           - Request for interview/next steps
           - Professional sign-off
        
        **Writing Guidelines:**
        - Keep to 3-4 paragraphs, maximum 1 page
        - Use specific examples and quantifiable achievements
        - Avoid generic templates - personalize for each application
        - Maintain professional yet engaging tone
        - Show research about the company and role
        - Use active voice and strong action verbs
        - Proofread for grammar and spelling
        
        **Tone Adaptation:**
        - Corporate/Traditional: Formal, conservative language
        - Startup/Tech: More casual, innovation-focused
        - Creative Industries: Show personality and creativity
        - Non-profit: Emphasize mission alignment and values
        
        Store the cover letter in the session state under 'cover_letter'.
        Also provide 'tone_analysis' explaining the approach taken.
        """
        
        super().__init__(
            name="CoverLetterGenerator",
            description="Creates personalized cover letters that highlight relevant achievements and demonstrate job fit",
            instruction=instruction,
            output_key="cover_letter",
            **kwargs
        )
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute cover letter generation logic.
        
        Args:
            context: The invocation context containing applicant and job data
            
        Yields:
            Event: Events with cover letter results
        """
        try:
            # Get applicant profile and job requirements from session state
            applicant_profile = self._get_applicant_profile(context)
            job_requirements = self._get_job_requirements(context)
            tailored_resume = self._get_tailored_resume(context)
            
            if not applicant_profile:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No applicant profile found for cover letter generation"}
                    )
                )
                return
            
            if not job_requirements:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No job requirements found for cover letter generation"}
                    )
                )
                return
            
            # Analyze company culture and determine appropriate tone
            tone_analysis = self._analyze_tone_requirements(job_requirements)
            
            # Extract key achievements for highlighting
            key_achievements = self._extract_key_achievements(applicant_profile, job_requirements)
            
            # Create enhanced instruction with specific data
            enhanced_instruction = f"""
            {self.instruction}
            
            **Applicant Profile:**
            {json.dumps(applicant_profile, indent=2)}
            
            **Job Requirements:**
            {json.dumps(job_requirements, indent=2)}
            
            **Tone Analysis:**
            {json.dumps(tone_analysis, indent=2)}
            
            **Key Achievements to Highlight:**
            {json.dumps(key_achievements, indent=2)}
            
            Based on this information, create a compelling cover letter that:
            1. Uses the appropriate tone for the company/industry
            2. Highlights the most relevant achievements
            3. Demonstrates clear understanding of the role and company
            4. Shows enthusiasm and cultural fit
            5. Includes a strong call-to-action
            
            Provide both the cover letter content and explanation of the tone/approach used.
            """
            
            # Update the agent's instruction temporarily
            original_instruction = self.instruction
            self.instruction = enhanced_instruction
            
            try:
                # Execute the LLM generation
                async for event in super()._execute_agent_logic(context):
                    # Process and validate the response
                    if event.actions and event.actions.state_delta:
                        self._enhance_cover_letter_results(event.actions.state_delta, tone_analysis)
                    yield event
            finally:
                # Restore original instruction
                self.instruction = original_instruction
                
        except Exception as e:
            yield Event(
                actions=EventActions(
                    state_delta={"cover_letter_error": str(e)}
                )
            )
    
    def _get_applicant_profile(self, context: InvocationContext) -> Optional[Dict[str, Any]]:
        """Extract applicant profile from context."""
        if not context.session or not context.session.state:
            return None
        return context.session.state.get('applicant_profile')
    
    def _get_job_requirements(self, context: InvocationContext) -> Optional[Dict[str, Any]]:
        """Extract job requirements from context."""
        if not context.session or not context.session.state:
            return None
        return context.session.state.get('job_requirements')
    
    def _get_tailored_resume(self, context: InvocationContext) -> Optional[str]:
        """Extract tailored resume from context."""
        if not context.session or not context.session.state:
            return None
        return context.session.state.get('tailored_resume')
    
    def _analyze_tone_requirements(self, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the job requirements to determine appropriate tone and style.
        
        Args:
            job_requirements: The job requirements data
            
        Returns:
            Tone analysis results
        """
        company_info = job_requirements.get('company_info', {})
        job_title = job_requirements.get('job_title', '').lower()
        company_culture = job_requirements.get('company_culture', {})
        
        # Determine industry and company type
        industry_indicators = {
            'tech': ['software', 'engineer', 'developer', 'programmer', 'tech', 'startup', 'saas'],
            'finance': ['financial', 'bank', 'investment', 'accounting', 'finance'],
            'healthcare': ['medical', 'health', 'hospital', 'clinical', 'pharmaceutical'],
            'education': ['teacher', 'professor', 'education', 'academic', 'university'],
            'creative': ['designer', 'creative', 'marketing', 'brand', 'content'],
            'nonprofit': ['nonprofit', 'charity', 'foundation', 'social impact']
        }
        
        detected_industry = 'corporate'  # default
        for industry, keywords in industry_indicators.items():
            if any(keyword in job_title for keyword in keywords):
                detected_industry = industry
                break
        
        # Determine formality level
        formality_level = 'professional'  # default
        if detected_industry in ['tech', 'creative']:
            formality_level = 'casual-professional'
        elif detected_industry in ['finance', 'healthcare']:
            formality_level = 'formal'
        
        # Analyze company culture indicators
        culture_values = []
        culture_text = str(company_culture).lower() if company_culture else ''
        
        culture_keywords = {
            'innovation': ['innovative', 'cutting-edge', 'disruptive', 'pioneering'],
            'collaboration': ['team', 'collaborative', 'together', 'partnership'],
            'growth': ['growth', 'learning', 'development', 'advancement'],
            'impact': ['impact', 'difference', 'change', 'mission'],
            'flexibility': ['flexible', 'remote', 'work-life', 'balance']
        }
        
        for value, keywords in culture_keywords.items():
            if any(keyword in culture_text for keyword in keywords):
                culture_values.append(value)
        
        return {
            'detected_industry': detected_industry,
            'formality_level': formality_level,
            'culture_values': culture_values,
            'tone_recommendations': {
                'opening_style': 'attention-grabbing' if detected_industry == 'creative' else 'professional',
                'body_style': 'achievement-focused',
                'closing_style': 'confident',
                'personality_level': 'moderate' if formality_level == 'formal' else 'high'
            }
        }
    
    def _extract_key_achievements(self, applicant_profile: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key achievements that are most relevant to the job.
        
        Args:
            applicant_profile: The applicant's profile data
            job_requirements: The job requirements data
            
        Returns:
            Key achievements to highlight
        """
        work_experience = applicant_profile.get('work_experience', [])
        achievements = applicant_profile.get('achievements', [])
        job_responsibilities = job_requirements.get('responsibilities', [])
        
        # Extract quantifiable achievements
        quantifiable_achievements = []
        achievement_keywords = ['increased', 'improved', 'reduced', 'saved', 'generated', 'led', 'managed', '%', '$']
        
        for exp in work_experience if isinstance(work_experience, list) else []:
            if isinstance(exp, dict) and 'achievements' in exp:
                for achievement in exp['achievements']:
                    if any(keyword in str(achievement).lower() for keyword in achievement_keywords):
                        quantifiable_achievements.append(achievement)
        
        # Add standalone achievements
        for achievement in achievements if isinstance(achievements, list) else []:
            if any(keyword in str(achievement).lower() for keyword in achievement_keywords):
                quantifiable_achievements.append(achievement)
        
        # Match achievements to job responsibilities
        relevant_achievements = []
        for achievement in quantifiable_achievements:
            achievement_text = str(achievement).lower()
            for responsibility in job_responsibilities:
                responsibility_text = str(responsibility).lower()
                # Simple keyword matching
                if any(word in responsibility_text for word in achievement_text.split() if len(word) > 3):
                    relevant_achievements.append(achievement)
                    break
        
        return {
            'quantifiable_achievements': quantifiable_achievements[:5],  # Top 5
            'relevant_achievements': relevant_achievements[:3],  # Top 3 most relevant
            'total_achievements_available': len(quantifiable_achievements)
        }
    
    def _enhance_cover_letter_results(self, state_delta: Dict[str, Any], tone_analysis: Dict[str, Any]) -> None:
        """
        Enhance the cover letter results with additional metadata.
        
        Args:
            state_delta: The state delta to enhance
            tone_analysis: The tone analysis performed
        """
        if 'cover_letter' in state_delta:
            # Add cover letter metadata
            state_delta['cover_letter_metadata'] = {
                'agent': self.name,
                'tone_analysis': tone_analysis,
                'personalization_level': 'high',
                'industry_adapted': True,
                'generation_completed': True
            }
            
            # Calculate personalization score (simplified)
            personalization_score = 0.8  # Base score
            if tone_analysis.get('culture_values'):
                personalization_score += 0.1
            if tone_analysis.get('detected_industry') != 'corporate':
                personalization_score += 0.1
            
            state_delta['personalization_score'] = min(1.0, personalization_score)
