"""Quality Reviewer agent for reviewing and validating final output quality."""

import json
from typing import Any, Dict, Optional, AsyncGenerator, List
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..base.llm_agent import ResumeBuilderLlmAgent


class QualityReviewer(ResumeBuilderLlmAgent):
    """
    Reviews and validates final output quality.
    
    This agent specializes in quality assurance, checking content accuracy,
    professional formatting, ATS compatibility, and providing improvement recommendations.
    """
    
    def __init__(self, quality_threshold: float = 0.85, **kwargs: Any) -> None:
        """
        Initialize the Quality Reviewer agent.
        
        Args:
            quality_threshold: Minimum quality score required for approval
        """
        instruction = """
        You are a Quality Assurance specialist for resume and cover letter review. Your role is to ensure all generated content meets professional standards and optimization requirements.
        
        **Primary Responsibilities:**
        1. Check content accuracy and relevance
        2. Ensure professional formatting and structure
        3. Validate ATS (Applicant Tracking System) compatibility
        4. Provide specific improvement recommendations
        5. Score overall quality and readiness
        
        **Quality Assessment Areas:**
        
        **Content Quality (30%):**
        - Accuracy of information
        - Relevance to job requirements
        - Clarity and coherence
        - Professional language use
        - Quantifiable achievements highlighted
        
        **ATS Optimization (25%):**
        - Keyword integration and density
        - Standard section headers
        - Bullet point formatting
        - File format compatibility
        - Consistent formatting
        
        **Professional Standards (25%):**
        - Grammar and spelling accuracy
        - Consistent formatting
        - Appropriate length
        - Professional tone
        - Industry-appropriate language
        
        **Alignment & Relevance (20%):**
        - Job requirement alignment
        - Skills matching
        - Experience prioritization
        - Company culture fit
        - Industry standards compliance
        
        **Review Process:**
        1. Analyze each document component
        2. Score each quality area (0-100)
        3. Calculate overall quality score
        4. Identify specific issues and improvements
        5. Provide actionable recommendations
        6. Determine if content meets approval threshold
        
        **Output Format:**
        Provide comprehensive review results including:
        - Overall quality score (0-100)
        - Component scores for each area
        - Specific issues identified
        - Improvement recommendations
        - ATS compatibility assessment
        - Approval status (approved/needs_revision)
        """
        
        super().__init__(
            name="QualityReviewer",
            description="Reviews and validates resume and cover letter quality with ATS optimization assessment",
            instruction=instruction,
            output_key="quality_review",
            **kwargs
        )
        
        self._quality_threshold = quality_threshold
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute quality review logic.
        
        Args:
            context: The invocation context containing generated content
            
        Yields:
            Event: Events with quality review results
        """
        try:
            # Get generated content from session state
            tailored_resume = self._get_tailored_resume(context)
            cover_letter = self._get_cover_letter(context)
            applicant_profile = self._get_applicant_profile(context)
            job_requirements = self._get_job_requirements(context)
            
            if not tailored_resume and not cover_letter:
                yield Event(
                    actions=EventActions(
                        state_delta={"error": "No content found for quality review"}
                    )
                )
                return
            
            # Perform preliminary analysis
            content_analysis = self._analyze_content_structure(tailored_resume, cover_letter)
            
            # Create enhanced instruction with specific content
            enhanced_instruction = f"""
            {self.instruction}
            
            **Generated Content to Review:**
            
            **Tailored Resume:**
            {tailored_resume or "Not provided"}
            
            **Cover Letter:**
            {cover_letter or "Not provided"}
            
            **Original Requirements:**
            Job Requirements: {json.dumps(job_requirements, indent=2) if job_requirements else "Not available"}
            Applicant Profile: {json.dumps(applicant_profile, indent=2) if applicant_profile else "Not available"}
            
            **Content Analysis:**
            {json.dumps(content_analysis, indent=2)}
            
            Please conduct a comprehensive quality review focusing on:
            1. Professional standards and formatting
            2. ATS optimization and keyword usage
            3. Alignment with job requirements
            4. Content accuracy and relevance
            5. Overall presentation quality
            
            Provide detailed scores, specific feedback, and actionable recommendations.
            Quality threshold for approval: {self._quality_threshold * 100}%
            """
            
            # Update the agent's instruction temporarily
            original_instruction = self.instruction
            self.instruction = enhanced_instruction
            
            try:
                # Execute the LLM review
                async for event in super()._execute_agent_logic(context):
                    # Process and validate the response
                    if event.actions and event.actions.state_delta:
                        self._enhance_review_results(event.actions.state_delta, content_analysis)
                    yield event
            finally:
                # Restore original instruction
                self.instruction = original_instruction
                
        except Exception as e:
            yield Event(
                actions=EventActions(
                    state_delta={"quality_review_error": str(e)}
                )
            )
    
    def _get_tailored_resume(self, context: InvocationContext) -> Optional[str]:
        """Extract tailored resume from context."""
        if not context.session or not context.session.state:
            return None
        return context.session.state.get('tailored_resume')
    
    def _get_cover_letter(self, context: InvocationContext) -> Optional[str]:
        """Extract cover letter from context."""
        if not context.session or not context.session.state:
            return None
        return context.session.state.get('cover_letter')
    
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
    
    def _analyze_content_structure(self, resume: Optional[str], cover_letter: Optional[str]) -> Dict[str, Any]:
        """
        Perform preliminary analysis of content structure.
        
        Args:
            resume: The tailored resume content
            cover_letter: The cover letter content
            
        Returns:
            Content analysis results
        """
        analysis = {
            'resume_analysis': {},
            'cover_letter_analysis': {},
            'overall_metrics': {}
        }
        
        # Analyze resume structure
        if resume:
            resume_analysis = self._analyze_resume_structure(resume)
            analysis['resume_analysis'] = resume_analysis
        
        # Analyze cover letter structure
        if cover_letter:
            cover_letter_analysis = self._analyze_cover_letter_structure(cover_letter)
            analysis['cover_letter_analysis'] = cover_letter_analysis
        
        # Overall metrics
        analysis['overall_metrics'] = {
            'has_resume': bool(resume),
            'has_cover_letter': bool(cover_letter),
            'total_content_length': len(resume or '') + len(cover_letter or ''),
            'documents_count': sum([bool(resume), bool(cover_letter)])
        }
        
        return analysis
    
    def _analyze_resume_structure(self, resume: str) -> Dict[str, Any]:
        """Analyze resume structure and content."""
        lines = resume.split('\n')
        
        # Check for common resume sections
        common_sections = [
            'professional summary', 'summary', 'objective',
            'experience', 'work experience', 'professional experience',
            'skills', 'technical skills', 'core competencies',
            'education', 'certifications', 'achievements'
        ]
        
        found_sections = []
        for line in lines:
            line_lower = line.lower().strip()
            for section in common_sections:
                if section in line_lower and len(line_lower) < 50:  # Likely a header
                    found_sections.append(section)
        
        # Count bullet points
        bullet_points = sum(1 for line in lines if line.strip().startswith(('•', '-', '*')))
        
        # Estimate word count
        word_count = len(resume.split())
        
        return {
            'total_lines': len(lines),
            'sections_found': list(set(found_sections)),
            'sections_count': len(set(found_sections)),
            'bullet_points': bullet_points,
            'word_count': word_count,
            'estimated_pages': max(1, word_count // 250),  # Rough estimate
            'has_contact_info': any(char in resume for char in ['@', '.com', '.org', '(']),
            'formatting_indicators': {
                'has_bullets': bullet_points > 0,
                'has_sections': len(found_sections) > 0,
                'appropriate_length': 100 <= word_count <= 800
            }
        }
    
    def _analyze_cover_letter_structure(self, cover_letter: str) -> Dict[str, Any]:
        """Analyze cover letter structure and content."""
        paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
        lines = cover_letter.split('\n')
        word_count = len(cover_letter.split())
        
        # Check for key components
        has_greeting = any('dear' in line.lower() for line in lines[:5])
        has_closing = any(closing in cover_letter.lower() for closing in [
            'sincerely', 'best regards', 'thank you', 'looking forward'
        ])
        
        # Check for personalization
        personalization_indicators = [
            'your company', 'your team', 'your organization',
            'this role', 'this position', 'your mission'
        ]
        personalization_score = sum(
            1 for indicator in personalization_indicators 
            if indicator in cover_letter.lower()
        )
        
        return {
            'paragraph_count': len(paragraphs),
            'total_lines': len(lines),
            'word_count': word_count,
            'has_greeting': has_greeting,
            'has_closing': has_closing,
            'personalization_score': personalization_score,
            'appropriate_length': 150 <= word_count <= 400,
            'structure_quality': {
                'proper_paragraph_count': 3 <= len(paragraphs) <= 5,
                'has_greeting': has_greeting,
                'has_closing': has_closing,
                'shows_personalization': personalization_score > 0
            }
        }
    
    def _enhance_review_results(self, state_delta: Dict[str, Any], content_analysis: Dict[str, Any]) -> None:
        """
        Enhance the review results with additional analysis and scoring.
        
        Args:
            state_delta: The state delta to enhance
            content_analysis: The preliminary content analysis
        """
        if 'quality_review' not in state_delta:
            return
        
        review = state_delta['quality_review']
        
        # Parse review if it's a string
        if isinstance(review, str):
            try:
                review = json.loads(review)
                state_delta['quality_review'] = review
            except json.JSONDecodeError:
                # If parsing fails, create a structured response
                state_delta['quality_review'] = {
                    'raw_review': review,
                    'parsing_error': True,
                    'overall_score': 0.7,  # Default score
                    'approved': False
                }
                return
        
        # Ensure required fields exist
        if 'overall_score' not in review:
            review['overall_score'] = 0.75  # Default
        
        # Normalize score to 0-1 range if it's 0-100
        overall_score = review['overall_score']
        if overall_score > 1:
            overall_score = overall_score / 100
            review['overall_score'] = overall_score
        
        # Determine approval status
        review['approved'] = overall_score >= self._quality_threshold
        
        # Add content analysis
        review['content_analysis'] = content_analysis
        
        # Add review metadata
        review['review_metadata'] = {
            'agent': self.name,
            'quality_threshold': self._quality_threshold,
            'review_completed': True,
            'recommendation': 'approved' if review['approved'] else 'needs_revision'
        }
        
        # Add improvement suggestions if score is low
        if overall_score < self._quality_threshold:
            if 'improvement_recommendations' not in review:
                review['improvement_recommendations'] = [
                    "Review and improve content alignment with job requirements",
                    "Enhance keyword optimization for ATS compatibility",
                    "Strengthen quantifiable achievements and results",
                    "Improve professional formatting and structure"
                ]
        
        state_delta['quality_review'] = review
        state_delta['quality_score'] = overall_score
