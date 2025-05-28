"""
Agent Router

This module defines the API endpoints for interacting with agents.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.auth import TokenData, require_jwt_auth
from ..services.agent_registry import AgentRegistry, AgentConfig
from ..agents.base import BaseAgent

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

# Initialize agent registry
agent_registry = AgentRegistry()

class AgentResponse(BaseModel):
    """Response model for agent information."""
    agent_id: str
    display_name: str
    description: str
    capabilities: List[str]
    example_queries: List[str]
    is_available: bool

class AgentQueryRequest(BaseModel):
    """Request model for querying an agent."""
    query: str = Field(..., min_length=1, max_length=1000)
    agent_id: str
    session_id: Optional[str] = None

class AgentQueryResponse(BaseModel):
    """Response model for agent query results."""
    answer: str
    trace_id: str
    ipfs_hash: str
    commitment_hash: str
    metadata: Dict

@router.get("/", response_model=List[AgentResponse])
async def list_agents(token_data: TokenData = Depends(require_jwt_auth)):
    """Get a list of all available agents."""
    try:
        agents = agent_registry.get_available_agents()
        return [
            AgentResponse(
                agent_id=agent_id,
                display_name=config.display_name,
                description=config.description,
                capabilities=config.capabilities,
                example_queries=config.example_queries,
                is_available=config.is_available
            )
            for agent_id, config in agents.items()
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    token_data: TokenData = Depends(require_jwt_auth)
):
    """Get detailed information about a specific agent."""
    try:
        config = agent_registry.get_agent_config(agent_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
            
        return AgentResponse(
            agent_id=agent_id,
            display_name=config.display_name,
            description=config.description,
            capabilities=config.capabilities,
            example_queries=config.example_queries,
            is_available=config.is_available
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    request: AgentQueryRequest,
    token_data: TokenData = Depends(require_jwt_auth)
):
    """Query an agent with a natural language question."""
    try:
        # Get agent configuration
        config = agent_registry.get_agent_config(request.agent_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {request.agent_id} not found"
            )
            
        if not config.is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Agent {request.agent_id} is currently unavailable"
            )
            
        # Get agent class
        agent_class = agent_registry.get_agent_class(request.agent_id)
        if not agent_class:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent implementation not found for {request.agent_id}"
            )
            
        # Create agent instance
        agent = agent_class(
            agent_id=f"{request.agent_id}_{token_data.wallet_address}",
            web3_provider=config.required_config.get("web3_provider")
        )
        
        # Initialize agent
        await agent.initialize()
        
        try:
            # Execute query
            result = await agent.execute(request.query)
            
            return AgentQueryResponse(
                answer=result["answer"],
                trace_id=result["trace_id"],
                ipfs_hash=result["ipfs_hash"],
                commitment_hash=result["commitment_hash"],
                metadata=result["trace_metadata"]
            )
            
        finally:
            # Clean up agent resources
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{agent_id}/capabilities", response_model=List[str])
async def get_agent_capabilities(
    agent_id: str,
    token_data: TokenData = Depends(require_jwt_auth)
):
    """Get the capabilities of a specific agent."""
    try:
        capabilities = agent_registry.get_agent_capabilities(agent_id)
        return capabilities
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{agent_id}/examples", response_model=List[str])
async def get_agent_examples(
    agent_id: str,
    token_data: TokenData = Depends(require_jwt_auth)
):
    """Get example queries for a specific agent."""
    try:
        examples = agent_registry.get_example_queries(agent_id)
        return examples
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 