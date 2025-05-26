"""
Base Agent Interface

This module defines the base interface that all agents must implement.
"""
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer


class ExecutionStep(BaseModel):
    """Represents a single step in the agent's execution trace."""
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={"description": "A single step in the agent's execution trace"}
    )
    
    step_id: str = Field(
        default_factory=lambda: str(uuid4()),
        json_schema_extra={"description": "Unique identifier for the step"}
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        json_schema_extra={"description": "When the step was executed"}
    )
    action: str = Field(
        json_schema_extra={"description": "The action being performed"}
    )
    inputs: Dict[str, Any] = Field(
        json_schema_extra={"description": "Input parameters for the action"}
    )
    outputs: Dict[str, Any] = Field(
        json_schema_extra={"description": "Output results from the action"}
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={"description": "Additional metadata about the step"}
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime) -> str:
        return dt.isoformat()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the serialized step."""
        serialized = json.dumps(
            self.model_dump(exclude={'step_id', 'timestamp'}),
            sort_keys=True,
            default=str
        )
        return hashlib.sha256(serialized.encode()).hexdigest()

class ExecutionTrace(BaseModel):
    """Represents a complete execution trace for an agent."""
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={"description": "A complete execution trace for an agent"}
    )
    
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        json_schema_extra={"description": "Unique identifier for the trace"}
    )
    agent_id: str = Field(
        json_schema_extra={"description": "Identifier of the agent that created the trace"}
    )
    start_time: datetime = Field(
        default_factory=datetime.utcnow,
        json_schema_extra={"description": "When the trace started"}
    )
    end_time: Optional[datetime] = Field(
        default=None,
        json_schema_extra={"description": "When the trace ended"}
    )
    steps: List[ExecutionStep] = Field(
        default_factory=list,
        json_schema_extra={"description": "List of execution steps"}
    )
    ipfs_hash: Optional[str] = Field(
        default=None,
        json_schema_extra={"description": "IPFS hash where the trace is stored"}
    )
    commitment_hash: Optional[str] = Field(
        default=None,
        json_schema_extra={"description": "Commitment hash for the trace"}
    )

    @field_serializer("start_time", "end_time")
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None

    def compute_root_hash(self) -> str:
        """
        Compute the root hash of the trace by hashing concatenated step hashes.
        
        Returns:
            str: SHA-256 hash of the concatenated step hashes
        """
        if not self.steps:
            return hashlib.sha256(b"").hexdigest()
            
        # Compute hash for each step
        step_hashes = [step.compute_hash() for step in self.steps]
        
        # Concatenate all step hashes and compute final hash
        concatenated = "".join(step_hashes)
        return hashlib.sha256(concatenated.encode()).hexdigest()

    def to_serializable_dict(self) -> Dict[str, Any]:
        """
        Convert the trace to a serializable dictionary, excluding None values.
        
        Returns:
            Dict[str, Any]: Serializable dictionary representation of the trace
        """
        return self.model_dump(exclude_none=True)

class BaseAgent(ABC):
    """Base class that all agents must inherit from."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_trace: Optional[ExecutionTrace] = None
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main functionality.
        Must be implemented by all agent subclasses.
        """
        pass
    
    async def log_step(self, action: str, inputs: Dict[str, Any], 
                      outputs: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ExecutionStep:
        """
        Log a single execution step.
        
        Args:
            action: The action being performed
            inputs: Input parameters for the action
            outputs: Output results from the action
            metadata: Additional metadata about the step (optional)
            
        Returns:
            ExecutionStep: The created step object
        """
        if not self.current_trace:
            self.current_trace = ExecutionTrace(agent_id=self.agent_id)
            
        step = ExecutionStep(
            action=action,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata or {}
        )
        self.current_trace.steps.append(step)
        return step
    
    async def finalize_trace(self) -> str:
        """
        Finalize the current trace by setting end time and computing commitment hash.
        
        Returns:
            str: The computed commitment hash
        """
        if not self.current_trace:
            raise ValueError("No active trace to finalize")
            
        self.current_trace.end_time = datetime.utcnow()
        commitment_hash = self.current_trace.compute_root_hash()
        self.current_trace.commitment_hash = commitment_hash
        return commitment_hash
    
    @abstractmethod
    async def store_trace(self) -> str:
        """
        Store the execution trace on IPFS and return the hash.
        Must be implemented by all agent subclasses.
        """
        pass
    
    @abstractmethod
    async def submit_commitment(self, ipfs_hash: str) -> str:
        """
        Submit a commitment hash for the trace.
        Must be implemented by all agent subclasses.
        """
        pass 