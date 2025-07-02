"""Base LLM agent implementation for the AI Resume Builder."""

from typing import Any, Dict, Optional, AsyncGenerator, List
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from .base_agent import ResumeBuilderBaseAgent


class ResumeBuilderLlmAgent(LlmAgent, ResumeBuilderBaseAgent):
    """
    Base LLM agent class for Resume Builder agents that use language models.
    
    This class extends both Google ADK's LlmAgent and our custom base agent,
    providing LLM capabilities with Resume Builder specific functionality.
    """
    
    def __init__(
        self,
        name: str,
        model: str = "gemini-2.0-flash-exp",
        description: Optional[str] = None,
        instruction: Optional[str] = None,
        global_instruction: Optional[str] = None,
        output_key: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the LLM agent.
        
        Args:
            name: The name of the agent
            model: The LLM model to use
            description: Optional description of the agent's purpose
            instruction: Specific instruction for this agent
            global_instruction: Global instruction for the agent
            output_key: Key to store output in session state
            tools: List of tools available to the agent
            **kwargs: Additional keyword arguments
        """
        # Prepare arguments for LlmAgent, excluding None values
        llm_args = {
            "name": name,
            "model": model,
            "tools": tools or [],
            **kwargs
        }
        
        if description is not None:
            llm_args["description"] = description
        if instruction is not None:
            llm_args["instruction"] = instruction
        if global_instruction is not None:
            llm_args["global_instruction"] = global_instruction
        if output_key is not None:
            llm_args["output_key"] = output_key
        
        # Initialize LlmAgent
        LlmAgent.__init__(self, **llm_args)
        
        # Initialize ResumeBuilderBaseAgent
        ResumeBuilderBaseAgent.__init__(self, name=name, description=description)
        
        self._model_name = model
        self._custom_tools = tools or []
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name
    
    @property
    def custom_tools(self) -> List[Any]:
        """Get the custom tools."""
        return self._custom_tools
    
    def _setup_resources(self) -> None:
        """Setup LLM-specific resources."""
        super()._setup_resources()
        # Additional LLM-specific setup can be added here
        pass
    
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute the LLM agent logic.
        
        Args:
            context: The invocation context
            
        Yields:
            Event: Events generated during execution
        """
        # Use the parent LlmAgent's run_async method
        async for event in LlmAgent.run_async(self, context):
            yield event
    
    def enhance_instruction_with_context(self, context: InvocationContext) -> str:
        """
        Enhance the agent's instruction with context-specific information.
        
        Args:
            context: The invocation context
            
        Returns:
            Enhanced instruction string
        """
        base_instruction = self.instruction or ""
        
        # Add context-specific enhancements
        context_info = []
        
        if hasattr(context, 'session') and context.session.state:
            state_keys = list(context.session.state.keys())
            if state_keys:
                context_info.append(f"Available state keys: {', '.join(state_keys)}")
        
        if context_info:
            enhanced_instruction = f"{base_instruction}\n\nContext Information:\n" + "\n".join(context_info)
            return enhanced_instruction
        
        return base_instruction
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this LLM agent.
        
        Returns:
            Dict containing agent information
        """
        info = super().get_agent_info()
        info.update({
            "model": self._model_name,
            "tools_count": len(self._custom_tools),
            "has_instruction": bool(self.instruction),
            "has_global_instruction": bool(self.global_instruction),
            "output_key": self.output_key
        })
        return info
