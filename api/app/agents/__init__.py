"""
NeuroSpace Agents Module

This module contains the implementation of various agents that can perform
on-chain operations and maintain verifiable execution traces.
"""

from .base import BaseAgent
from .onchain_qa import OnChainQAAgent

__all__ = ['BaseAgent', 'OnChainQAAgent'] 