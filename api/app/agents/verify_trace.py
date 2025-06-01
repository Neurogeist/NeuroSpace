#!/usr/bin/env python3
"""
Trace Verification Script

This script verifies the integrity of an execution trace by:
1. Loading the trace from IPFS or a local file
2. Recomputing step hashes
3. Verifying the commitment hash
4. Reporting any mismatches
"""
import argparse
import asyncio
import hashlib
import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.ipfs import IPFSService
from ..core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TraceVerifier:
    """Verifies the integrity of execution traces."""
    
    def __init__(self):
        settings = get_settings()
        # Use local IPFS gateway for development
        self.ipfs_service = IPFSService(
            ipfs_gateway=settings.ipfs_gateway_url
        )
    
    def compute_step_hash(self, step: Dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of a step using the same logic as ExecutionStep.
        
        Args:
            step: Step data from the trace
            
        Returns:
            str: SHA-256 hash of the step
        """
        # Create a copy of the step data excluding step_id and timestamp
        step_data = {
            "action": step["action"],
            "inputs": step["inputs"],
            "outputs": step["outputs"],
            "metadata": step.get("metadata", {})
        }
        
        # Sort keys to ensure consistent hashing
        serialized = json.dumps(step_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def compute_commitment_hash(self, steps: list) -> str:
        """
        Compute the commitment hash by hashing concatenated step hashes.
        
        Args:
            steps: List of step data from the trace
            
        Returns:
            str: SHA-256 hash of concatenated step hashes
        """
        if not steps:
            return hashlib.sha256(b"").hexdigest()
            
        # Compute hash for each step
        step_hashes = [self.compute_step_hash(step) for step in steps]
        
        # Concatenate all step hashes and compute final hash
        concatenated = "".join(step_hashes)
        return hashlib.sha256(concatenated.encode()).hexdigest()
    
    async def verify_trace(self, trace_data: Dict[str, Any], verbose: bool = False) -> bool:
        """
        Verify the integrity of a trace.
        
        Args:
            trace_data: The trace data to verify
            verbose: Whether to print detailed information
            
        Returns:
            bool: True if trace is valid, False otherwise
        """
        try:
            # Get stored commitment hash
            stored_hash = trace_data.get('commitment_hash')
            if not stored_hash:
                logger.error("No commitment hash found in trace")
                return False
            
            # Compute commitment hash from steps
            computed_hash = self.compute_commitment_hash(trace_data.get('steps', []))
            
            # Compare hashes
            if stored_hash != computed_hash:
                if verbose:
                    logger.error(f"Hash mismatch!\nStored: {stored_hash}\nComputed: {computed_hash}")
                    
                    # Check individual step hashes
                    for i, step in enumerate(trace_data.get('steps', [])):
                        stored_step_hash = step.get('step_hash')
                        computed_step_hash = self.compute_step_hash(step)
                        if stored_step_hash != computed_step_hash:
                            logger.error(f"Step {i} hash mismatch!")
                            logger.error(f"Stored: {stored_step_hash}")
                            logger.error(f"Computed: {computed_step_hash}")
                            if verbose:
                                logger.error("Step data:")
                                logger.error(json.dumps(step, indent=2))
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying trace: {str(e)}")
            return False
    
    async def load_trace(self, ipfs_hash: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load trace data from IPFS or local file.
        
        Args:
            ipfs_hash: IPFS hash to load from
            file_path: Local file path to load from
            
        Returns:
            Dict[str, Any]: The loaded trace data
            
        Raises:
            ValueError: If neither ipfs_hash nor file_path is provided
        """
        if ipfs_hash:
            logger.info(f"Loading trace from IPFS: {ipfs_hash}")
            try:
                return await self.ipfs_service.download_json(ipfs_hash)
            except Exception as e:
                logger.error(f"Failed to download from IPFS: {str(e)}")
                # Try using the API endpoint as fallback
                logger.info("Trying API endpoint as fallback...")
                return await self.ipfs_service.get_from_ipfs(ipfs_hash)
        elif file_path:
            logger.info(f"Loading trace from file: {file_path}")
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            raise ValueError("Either ipfs_hash or file_path must be provided")

async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Verify execution trace integrity")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ipfs-hash", help="IPFS hash (CID) of the trace")
    group.add_argument("--file", help="Path to local trace file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed verification info")
    
    args = parser.parse_args()
    
    try:
        verifier = TraceVerifier()
        trace_data = await verifier.load_trace(args.ipfs_hash, args.file)
        
        logger.info("Verifying trace integrity...")
        is_valid = await verifier.verify_trace(trace_data, args.verbose)
        
        if is_valid:
            logger.info("✅ Trace is valid!")
            if args.verbose:
                logger.info(f"Trace ID: {trace_data['trace_id']}")
                logger.info(f"Agent ID: {trace_data['agent_id']}")
                logger.info(f"Steps: {len(trace_data['steps'])}")
                logger.info(f"Commitment hash: {trace_data['commitment_hash']}")
        else:
            logger.error("❌ Trace is invalid!")
            if trace_data.get('steps', []):
                logger.error(f"Found {len(trace_data['steps'])} mismatched steps:")
                for i, step in enumerate(trace_data['steps']):
                    logger.error(f"Step {i} ({step['action']}):")
                    logger.error(f"  Computed: {verifier.compute_step_hash(step)}")
                    logger.error(f"  Stored:   {step.get('step_hash')}")
                    if args.verbose:
                        logger.error("  Step data:")
                        logger.error(json.dumps(step, indent=2))
        
        return 0 if is_valid else 1
        
    except Exception as e:
        logger.error(f"Error verifying trace: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 