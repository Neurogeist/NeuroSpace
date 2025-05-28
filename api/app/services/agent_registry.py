"""
Agent Registry Service

This service manages the registration and configuration of different agent types.
Similar to the model registry, it provides a central place to define and access
available agent types and their configurations.
"""
import logging
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field
from datetime import datetime

from ..agents.base import BaseAgent
from ..agents.onchain_qa import OnChainQAAgent

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration for an agent type."""
    agent_id: str
    display_name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    required_config: Dict[str, str] = Field(default_factory=dict)  # e.g., {"web3_provider": "WEB3_PROVIDER"}
    example_queries: List[str] = Field(default_factory=list)
    max_concurrent_requests: int = 10
    rate_limit_per_minute: int = 60
    is_available: bool = True

class AgentRegistry:
    """Registry for managing different agent types and their configurations."""
    
    def __init__(self):
        """Initialize the agent registry with available agent types."""
        # Define available agents with their configurations
        self.agents = {
            "onchain_qa": AgentConfig(
                agent_id="onchain_qa",
                display_name="On-Chain QA Agent",
                description="Answers questions about on-chain data and maintains verifiable execution traces",
                capabilities=[
                    "query_erc20_tokens",
                    "get_token_balances",
                    "get_token_supply",
                    "verify_execution_traces"
                ],
                required_config={
                    "web3_provider": "WEB3_PROVIDER"
                },
                example_queries=[
                    "What is the total supply of USDC?",
                    "What is the balance of 0x123... for WETH?",
                    "How many decimals does NEURO have?"
                ],
                max_concurrent_requests=10,
                rate_limit_per_minute=60
            )
        }
        
        # Map agent types to their implementation classes
        self._agent_classes: Dict[str, Type[BaseAgent]] = {
            "onchain_qa": OnChainQAAgent
        }
    
    def get_available_agents(self) -> Dict[str, AgentConfig]:
        """Get a dictionary of available agents with their configurations."""
        return {name: config for name, config in self.agents.items() if config.is_available}
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get the configuration for a specific agent type."""
        return self.agents.get(agent_id)
    
    def get_agent_class(self, agent_id: str) -> Optional[Type[BaseAgent]]:
        """Get the implementation class for a specific agent type."""
        return self._agent_classes.get(agent_id)
    
    def register_agent_type(self, agent_id: str, agent_class: Type[BaseAgent], config: AgentConfig) -> None:
        """
        Register a new agent type.
        
        Args:
            agent_id: Unique identifier for the agent type
            agent_class: The agent class to register
            config: Configuration for the agent type
        """
        if agent_id in self.agents:
            raise ValueError(f"Agent type {agent_id} already registered")
            
        self.agents[agent_id] = config
        self._agent_classes[agent_id] = agent_class
        logger.info(f"Registered new agent type: {agent_id}")
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get the capabilities of an agent type."""
        config = self.get_agent_config(agent_id)
        if not config:
            raise ValueError(f"Agent type {agent_id} not found")
        return config.capabilities
    
    def get_required_config(self, agent_id: str) -> Dict[str, str]:
        """Get the required configuration for an agent type."""
        config = self.get_agent_config(agent_id)
        if not config:
            raise ValueError(f"Agent type {agent_id} not found")
        return config.required_config
    
    def get_example_queries(self, agent_id: str) -> List[str]:
        """Get example queries for an agent type."""
        config = self.get_agent_config(agent_id)
        if not config:
            raise ValueError(f"Agent type {agent_id} not found")
        return config.example_queries 