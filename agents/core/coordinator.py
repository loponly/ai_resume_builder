"""Resume Builder Coordinator - Main orchestrator agent."""

import uuid
from typing import Any, Dict, Optional, AsyncGenerator, List
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from ..base.llm_agent import ResumeBuilderLlmAgent


class ResumeBuilderCoordinator(ResumeBuilderLlmAgent):
    """
    Main orchestrator agent that routes incoming requests and manages the overall workflow.
    
    This agent coordinates the entire resume building pipeline, delegating tasks to
    specialized agents and managing the overall process flow.
    """
    
    def __init__(self, sub_agents: Optional[List[Any]] = None, **kwargs: Any) -> None:
        """
        Initialize the Resume Builder Coordinator.
        
        Args:
            sub_agents: List of sub-agents to coordinate
        """
        print(f"🔧 Coordinator init: received {len(sub_agents) if sub_agents else 0} sub-agents")
        if sub_agents:
            print(f"🔧 Sub-agent names: {[agent.name for agent in sub_agents]}")
        
        instruction = """
        You are the Resume Builder Coordinator, the main orchestrator for the AI Resume Builder system.
        
        **Primary Responsibilities:**
        1. Parse and validate user inputs (CV and job description files)
        2. Coordinate the overall resume building workflow
        3. Manage communication between specialized agents
        4. Ensure quality standards are met
        5. Return final optimized documents to users
        
        **Workflow Overview:**
        1. Input Processing: Validate and prepare CV and job description content
        2. Analysis Phase: Coordinate CV analysis and job requirement extraction
        3. Generation Phase: Orchestrate resume tailoring and cover letter creation
        4. Quality Assurance: Ensure output meets professional standards
        5. Delivery: Present final documents to user
        
        **Quality Standards:**
        - All outputs must be professional and accurate
        - Content must be ATS-optimized
        - Alignment with job requirements is essential
        - Maintain applicant's authentic voice and experiences
        
        **Error Handling:**
        - Validate all inputs before processing
        - Handle failures gracefully with informative messages
        - Ensure partial results are available if possible
        - Provide clear feedback on any issues
        
        As the coordinator, you orchestrate the entire process but delegate specialized tasks to your sub-agents.
        """
        
        super().__init__(
            name="ResumeBuilderCoordinator",
            instruction=instruction,
            sub_agents=sub_agents or [],
            **kwargs
        )
        
        self._session_id = None
        self._processing_status = "idle"
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute the coordination logic.
        
        Args:
            context: The invocation context
            
        Yields:
            Event: Events from the coordination process
        """
        try:
            # Initialize session
            self._session_id = str(uuid.uuid4())
            self._processing_status = "initializing"
            
            print(f"🔧 Coordinator initialized with session: {self._session_id}")
            print(f"🔧 Sub-agents available: {[agent.name for agent in self.sub_agents]}")
            
            # Add session metadata to state
            yield Event(
                author=self.name,
                actions=EventActions(
                    state_delta={
                        "session_id": self._session_id,
                        "coordinator_status": "initialized",
                        "processing_stage": "input_validation"
                    }
                )
            )
            
            # Validate inputs
            validation_result = await self._validate_inputs(context)
            if not validation_result["valid"]:
                yield Event(
                    author=self.name,
                    actions=EventActions(
                        state_delta={
                            "error": validation_result["error"],
                            "coordinator_status": "failed",
                            "processing_stage": "validation_failed"
                        }
                    )
                )
                return
            
            # Update processing status
            self._processing_status = "processing"
            yield Event(
                author=self.name,
                actions=EventActions(
                    state_delta={
                        "coordinator_status": "processing",
                        "processing_stage": "workflow_started",
                        "input_validation": "passed"
                    }
                )
            )
            
            # Since we're using the workflow agents to orchestrate the actual pipeline,
            # the coordinator primarily handles initialization and monitoring
            
            # The actual workflow execution will be handled by the workflow agents
            # that are sub-agents of this coordinator
            
            # Execute sub-agents if they exist
            if self.sub_agents:
                print(f"🔧 Running {len(self.sub_agents)} sub-agents...")
                for sub_agent in self.sub_agents:
                    print(f"🔧 Executing sub-agent: {sub_agent.name}")
                    try:
                        async for event in sub_agent.run_async(context):
                            print(f"🔧 Event from {sub_agent.name}: {event.author if hasattr(event, 'author') else 'no author'}")
                            yield event
                    except Exception as e:
                        print(f"❌ Error in sub-agent {sub_agent.name}: {str(e)}")
                        yield Event(
                            author=self.name,
                            actions=EventActions(
                                state_delta={
                                    f"{sub_agent.name}_error": str(e),
                                    "coordinator_status": "partial_failure"
                                }
                            )
                        )
            else:
                print("⚠️ No sub-agents configured for coordinator - using direct LLM processing")
                
                # Get input data from the session state or context
                cv_content = context.session.state.get("cv_content", "")
                job_description = context.session.state.get("job_description", "")
                
                # Process directly using the LLM's built-in functionality
                # This will trigger the LLM to generate a response based on the user input
                # Since this is an LLM agent, it will automatically respond to the user content
                yield Event(
                    author=self.name,
                    actions=EventActions(
                        state_delta={
                            "coordinator_status": "direct_llm_processing",
                            "processing_stage": "llm_analysis",
                            "input_received": True,
                            "cv_length": len(cv_content),
                            "job_length": len(job_description)
                        }
                    )
                )
                
                # Let the parent LLM agent handle the actual processing
                # by not overriding its behavior completely
                return
            
            # Final coordination summary
            self._processing_status = "completed"
            yield Event(
                author=self.name,
                actions=EventActions(
                    state_delta={
                        "coordinator_status": "completed",
                        "processing_stage": "workflow_completed",
                        "session_summary": await self._generate_session_summary(context)
                    }
                )
            )
            
        except Exception as e:
            self._processing_status = "failed"
            yield Event(
                author=self.name,
                actions=EventActions(
                    state_delta={
                        "coordinator_error": str(e),
                        "coordinator_status": "failed",
                        "processing_stage": "coordinator_error"
                    }
                )
            )
    
    async def _validate_inputs(self, context: InvocationContext) -> Dict[str, Any]:
        """
        Validate the input data for processing.
        
        Args:
            context: The invocation context
            
        Returns:
            Validation results
        """
        if not context.session or not context.session.state:
            return {
                "valid": False,
                "error": "No session state available"
            }
        
        state = context.session.state
        
        # Check for required inputs
        cv_content = None
        job_content = None
        
        # Try to find CV content
        cv_keys = ['cv_content', 'cv_text', 'resume_content', 'original_cv']
        for key in cv_keys:
            if key in state and state[key]:
                cv_content = state[key]
                break
        
        # Try to find job description content
        job_keys = ['job_description', 'job_content', 'jd_content', 'job_text']
        for key in job_keys:
            if key in state and state[key]:
                job_content = state[key]
                break
        
        # Validate content
        errors = []
        
        if not cv_content:
            errors.append("CV content is required")
        elif len(str(cv_content).strip()) < 50:
            errors.append("CV content is too short (minimum 50 characters)")
        
        if not job_content:
            errors.append("Job description content is required")
        elif len(str(job_content).strip()) < 30:
            errors.append("Job description content is too short (minimum 30 characters)")
        
        if errors:
            return {
                "valid": False,
                "error": "; ".join(errors)
            }
        
        return {
            "valid": True,
            "cv_length": len(str(cv_content)),
            "job_length": len(str(job_content))
        }
    
    async def _generate_session_summary(self, context: InvocationContext) -> Dict[str, Any]:
        """
        Generate a summary of the processing session.
        
        Args:
            context: The invocation context
            
        Returns:
            Session summary
        """
        if not context.session or not context.session.state:
            return {"error": "No session state available"}
        
        state = context.session.state
        
        summary = {
            "session_id": self._session_id,
            "processing_status": self._processing_status,
            "components_generated": [],
            "quality_metrics": {},
            "errors": []
        }
        
        # Check what components were generated
        if 'applicant_profile' in state:
            summary["components_generated"].append("applicant_profile")
        
        if 'job_requirements' in state:
            summary["components_generated"].append("job_requirements")
        
        if 'tailored_resume' in state:
            summary["components_generated"].append("tailored_resume")
        
        if 'cover_letter' in state:
            summary["components_generated"].append("cover_letter")
        
        # Collect quality metrics
        if 'quality_score' in state:
            summary["quality_metrics"]["overall_quality"] = state['quality_score']
        
        if 'ats_score' in state:
            summary["quality_metrics"]["ats_compatibility"] = state['ats_score']
        
        if 'personalization_score' in state:
            summary["quality_metrics"]["personalization"] = state['personalization_score']
        
        # Collect any errors
        error_keys = [key for key in state.keys() if 'error' in key.lower()]
        for error_key in error_keys:
            summary["errors"].append({
                "component": error_key,
                "error": state[error_key]
            })
        
        return summary
    
    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id
    
    @property
    def processing_status(self) -> str:
        """Get the current processing status."""
        return self._processing_status
