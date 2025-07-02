"""Loop workflow agent for iterative processing."""

from typing import Any, List, Optional
from google.adk.agents import LoopAgent


class ResumeBuilderLoopAgent(LoopAgent):
    """
    Loop workflow agent for Resume Builder.
    
    This agent executes sub-agents in a loop until a termination condition is met,
    perfect for iterative refinement processes.
    """
    
    def __init__(
        self,
        name: str,
        sub_agents: List[Any],
        max_iterations: int = 3,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the loop workflow agent.
        
        Args:
            name: The name of the workflow agent
            sub_agents: List of agents to execute in loop
            max_iterations: Maximum number of iterations
            description: Optional description
        """
        # Initialize LoopAgent only
        super().__init__(
            name=name,
            sub_agents=sub_agents,
            max_iterations=max_iterations,
            description=description or f"Loop workflow with {len(sub_agents)} agents, max {max_iterations} iterations",
            **kwargs
        )
        
        self._sub_agents = sub_agents
        self._max_iterations = max_iterations
    
    def get_agent_info(self) -> dict:
        """Get information about this workflow agent."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "workflow_type": "loop",
            "max_iterations": self._max_iterations,
            "sub_agents_count": len(self._sub_agents),
            "sub_agent_names": [agent.name for agent in self._sub_agents]
        }
        return info
