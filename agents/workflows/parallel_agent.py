"""Parallel workflow agent for concurrent processing."""

from typing import Any, List, Optional
from google.adk.agents import ParallelAgent


class ResumeBuilderParallelAgent(ParallelAgent):
    """
    Parallel workflow agent for Resume Builder.
    
    This agent executes sub-agents concurrently, perfect for independent tasks
    that can run simultaneously to improve performance.
    """
    
    def __init__(
        self,
        name: str,
        sub_agents: List[Any],
        description: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the parallel workflow agent.
        
        Args:
            name: The name of the workflow agent
            sub_agents: List of agents to execute in parallel
            description: Optional description
        """
        # Initialize ParallelAgent
        super().__init__(
            name=name,
            sub_agents=sub_agents,
            description=description,
            **kwargs
        )
        
        self._sub_agents = sub_agents
    
    def get_agent_info(self) -> dict:
        """Get information about this workflow agent."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "workflow_type": "parallel",
            "sub_agents_count": len(self._sub_agents),
            "sub_agent_names": [agent.name for agent in self._sub_agents]
        }
