"""Resume Tailor agent for optimizing CV content for specific job requirements."""

import json
from typing import Any, Dict, Optional, AsyncGenerator, List
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.llm_agent import ResumeBuilderLlmAgent


class ResumeTailor(ResumeBuilderLlmAgent):
    """
    Optimizes CV content for specific job requirements.
    
    This agent specializes in matching applicant skills with job requirements,
    prioritizing relevant experiences, and optimizing content for ATS systems.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Resume Tailor agent."""
        instruction = """
        You are a Resume Tailoring specialist. Your role is to optimize CV content for specific job requirements.
        
        **Primary Responsibilities:**
        1. Match applicant skills with job requirements
        2. Prioritize relevant experiences and achievements
        3. Optimize keyword density for ATS systems
        4. Generate tailored resume content that highlights best fit
        5. Ensure professional formatting and structure
        
        **Tailoring Strategy:**
        1. Analyze skill overlap between CV and job requirements
        2. Prioritize experiences that match job responsibilities
        3. Highlight quantifiable achievements relevant to the role
        4. Integrate job-specific keywords naturally
        5. Adjust professional summary for the target role
        6. Reorder sections to emphasize most relevant qualifications
        
        **Output Format:**
        Provide a complete tailored resume with the following structure:
        - Professional Summary (tailored to the job)
        - Core Skills (prioritized and keyword-optimized)
        - Professional Experience (reordered and enhanced)
        - Education (relevant details highlighted)
        - Certifications (if relevant)
        - Additional sections as appropriate
        
        **Quality Standards:**
        - Maintain truthfulness (no fabrication)
        - Ensure ATS compatibility
        - Use strong action verbs and quantifiable results
        - Keep consistent professional tone
        - Optimize length (1-2 pages recommended)
        
        Store the tailored resume in the session state under 'tailored_resume'.
        Also provide a 'tailoring_strategy' explaining the optimization approach.
        """
        
        super().__init__(
            name="ResumeTailor",
            description="Optimizes CV content for specific job requirements with ATS optimization",
            instruction=instruction,
            output_key="tailored_resume",
            **kwargs
        )
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute resume tailoring logic.
        
        Args:
            context: The invocation context containing applicant and job data
            
        Yields:
            Event: Events with tailored resume results
        """
        try:
            # Get applicant profile and job requirements from session state
            applicant_profile = self._get_applicant_profile(context)
            job_requirements = self._get_job_requirements(context)
            
            if not applicant_profile:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No applicant profile found for tailoring"}
                    )
                )
                return
            
            if not job_requirements:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No job requirements found for tailoring"}
                    )
                )
                return
            
            # Analyze the match between applicant and job
            match_analysis = self._analyze_skill_match(applicant_profile, job_requirements)
            
            # Create enhanced instruction with specific data
            enhanced_instruction = f"""
            {self.instruction}
            
            **Applicant Profile:**
            {json.dumps(applicant_profile, indent=2)}
            
            **Job Requirements:**
            {json.dumps(job_requirements, indent=2)}
            
            **Skill Match Analysis:**
            {json.dumps(match_analysis, indent=2)}
            
            Based on this information, create a tailored resume that maximizes the alignment 
            between the applicant's background and the job requirements. Focus on:
            1. Highlighting matching skills and experiences
            2. Using keywords from the job description
            3. Quantifying achievements relevant to the role
            4. Structuring content for maximum impact
            
            Provide both the tailored resume content and a strategy explanation.
            """
            
            # Update the agent's instruction temporarily
            original_instruction = self.instruction
            self.instruction = enhanced_instruction
            
            try:
                # Execute the LLM tailoring
                async for event in super()._execute_agent_logic(context):
                    # Process and validate the response
                    if event.actions and event.actions.state_delta:
                        self._enhance_tailoring_results(event.actions.state_delta, match_analysis)
                    yield event
            finally:
                # Restore original instruction
                self.instruction = original_instruction
                
        except Exception as e:
            yield Event(
                actions=EventActions(
                    state_delta={"resume_tailoring_error": str(e)}
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
    
    def _analyze_skill_match(self, applicant_profile: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the match between applicant skills and job requirements.
        
        Args:
            applicant_profile: The applicant's profile data
            job_requirements: The job requirements data
            
        Returns:
            Match analysis results
        """
        # Extract skills from applicant profile
        applicant_skills = []
        if 'skills' in applicant_profile:
            skills_data = applicant_profile['skills']
            if isinstance(skills_data, dict):
                for category, skills in skills_data.items():
                    if isinstance(skills, list):
                        applicant_skills.extend([str(skill).lower() for skill in skills])
                    elif isinstance(skills, str):
                        applicant_skills.extend([s.strip().lower() for s in skills.split(',')])
            elif isinstance(skills_data, list):
                applicant_skills = [str(skill).lower() for skill in skills_data]
        
        # Extract required and preferred skills from job
        job_required = []
        job_preferred = []
        
        if 'required_skills' in job_requirements:
            job_required = [str(skill).lower() for skill in job_requirements['required_skills']]
        
        if 'preferred_skills' in job_requirements:
            job_preferred = [str(skill).lower() for skill in job_requirements['preferred_skills']]
        
        # Find matches
        required_matches = [skill for skill in job_required if any(skill in app_skill or app_skill in skill for app_skill in applicant_skills)]
        preferred_matches = [skill for skill in job_preferred if any(skill in app_skill or app_skill in skill for app_skill in applicant_skills)]
        
        # Calculate match scores
        required_score = len(required_matches) / max(len(job_required), 1) if job_required else 1.0
        preferred_score = len(preferred_matches) / max(len(job_preferred), 1) if job_preferred else 1.0
        overall_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        return {
            'required_matches': required_matches,
            'preferred_matches': preferred_matches,
            'missing_required': [skill for skill in job_required if skill not in required_matches],
            'missing_preferred': [skill for skill in job_preferred if skill not in preferred_matches],
            'match_scores': {
                'required': round(required_score, 2),
                'preferred': round(preferred_score, 2),
                'overall': round(overall_score, 2)
            },
            'recommendations': self._generate_recommendations(required_matches, job_required, job_preferred)
        }
    
    def _generate_recommendations(self, matches: List[str], required: List[str], preferred: List[str]) -> List[str]:
        """Generate tailoring recommendations based on skill analysis."""
        recommendations = []
        
        if len(matches) > 0:
            recommendations.append(f"Emphasize the {len(matches)} matching skills prominently")
        
        missing_critical = [skill for skill in required if skill not in matches]
        if missing_critical:
            recommendations.append(f"Address missing critical skills: {', '.join(missing_critical[:3])}")
        
        if len(preferred) > 0:
            recommendations.append("Incorporate preferred skills where possible")
        
        recommendations.append("Use job-specific keywords throughout the resume")
        recommendations.append("Quantify achievements that align with job responsibilities")
        
        return recommendations
    
    def _enhance_tailoring_results(self, state_delta: Dict[str, Any], match_analysis: Dict[str, Any]) -> None:
        """
        Enhance the tailoring results with additional metadata.
        
        Args:
            state_delta: The state delta to enhance
            match_analysis: The skill match analysis
        """
        if 'tailored_resume' in state_delta:
            # Add tailoring metadata
            state_delta['tailoring_metadata'] = {
                'agent': self.name,
                'match_score': match_analysis['match_scores']['overall'],
                'skills_matched': len(match_analysis['required_matches']) + len(match_analysis['preferred_matches']),
                'optimization_completed': True,
                'ats_optimized': True
            }
            
            # Add the match analysis to state
            state_delta['skill_match_analysis'] = match_analysis
            
            # Calculate and add ATS score (simplified)
            ats_score = min(0.95, 0.6 + (match_analysis['match_scores']['overall'] * 0.35))
            state_delta['ats_score'] = round(ats_score, 2)
