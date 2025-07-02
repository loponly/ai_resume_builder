"""Abstract base agent class for the AI Resume Builder."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class ResumeBuilderBaseAgent(BaseAgent, ABC):
    """
    Abstract base agent class for all Resume Builder agents.
    
    This class provides common functionality and interface for all agents
    in the Resume Builder system, following SOLID principles.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            description: Optional description of the agent's purpose
            **kwargs: Additional keyword arguments
        """
        super().__init__(name=name, description=description, **kwargs)
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized
    
    def initialize(self) -> None:
        """Initialize the agent with required resources."""
        if not self._initialized:
            self._setup_resources()
            self._initialized = True
    
    def _setup_resources(self) -> None:
        """Setup any required resources for the agent."""
        pass
    
    async def run_async(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Run the agent asynchronously.
        
        Args:
            context: The invocation context
            
        Yields:
            Event: Events generated during agent execution
        """
        # Ensure agent is initialized
        if not self._initialized:
            self.initialize()
        
        # Validate input
        await self._validate_input(context)
        
        # Execute agent logic
        async for event in self._execute_agent_logic(context):
            yield event
    
    async def _validate_input(self, context: InvocationContext) -> None:
        """
        Validate the input context.
        
        Args:
            context: The invocation context to validate
            
        Raises:
            ValueError: If input validation fails
        """
        if not context:
            raise ValueError("Context cannot be None")
    
    @abstractmethod
    async def _execute_agent_logic(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute the core agent logic.
        
        Args:
            context: The invocation context
            
        Yields:
            Event: Events generated during execution
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dict containing agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "initialized": self._initialized
        }
