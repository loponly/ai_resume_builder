"""Sequential workflow agent for step-by-step processing."""

from typing import Any, List, Optional
from google.adk.agents import SequentialAgent


class ResumeBuilderSequentialAgent(SequentialAgent):
    """
    Sequential workflow agent for Resume Builder.
    
    This agent executes sub-agents one after another in a defined order,
    perfect for pipeline-style processing where each step depends on the previous one.
    """
    
    def __init__(
        self,
        name: str,
        sub_agents: List[Any],
        description: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the sequential workflow agent.
        
        Args:
            name: The name of the workflow agent
            sub_agents: List of agents to execute sequentially
            description: Optional description
        """
        # Initialize SequentialAgent only
        super().__init__(
            name=name,
            sub_agents=sub_agents,
            description=description or f"Sequential workflow with {len(sub_agents)} agents",
            **kwargs
        )
        
        self._sub_agents = sub_agents
    
    def get_agent_info(self) -> dict:
        """Get information about this workflow agent."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "sub_agents": [agent.name for agent in self._sub_agents]
        }
        info.update({
            "workflow_type": "sequential",
            "sub_agents_count": len(self._sub_agents),
            "sub_agent_names": [agent.name for agent in self._sub_agents]
        })
        return info
