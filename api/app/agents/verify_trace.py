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
import hashlib
import json
import logging
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..services.ipfs import IPFSService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TraceVerifier:
    """Verifies the integrity of execution traces."""
    
    def __init__(self):
        self.ipfs_service = IPFSService()
    
    def compute_step_hash(self, step: Dict) -> str:
        """
        Compute SHA-256 hash of a step using the same logic as ExecutionStep.
        
        Args:
            step: Step data dictionary
            
        Returns:
            str: SHA-256 hash of the step
        """
        # Create a copy of the step data excluding step_id and timestamp
        step_data = {
            "action": step["action"],
            "inputs": step["inputs"],
            "outputs": step["outputs"],
            "metadata": step["metadata"]
        }
        
        # Sort keys to ensure consistent ordering
        serialized = json.dumps(step_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def compute_commitment_hash(self, step_hashes: List[str]) -> str:
        """
        Compute the commitment hash from step hashes.
        
        Args:
            step_hashes: List of step hashes
            
        Returns:
            str: Commitment hash
        """
        if not step_hashes:
            return hashlib.sha256(b"").hexdigest()
        
        # Concatenate all step hashes and compute final hash
        concatenated = "".join(step_hashes)
        return hashlib.sha256(concatenated.encode()).hexdigest()
    
    def verify_trace(self, trace_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Verify the integrity of a trace.
        
        Args:
            trace_data: Trace data dictionary
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, list of mismatched steps)
        """
        mismatches = []
        step_hashes = []
        
        # Verify each step
        for i, step in enumerate(trace_data["steps"]):
            computed_hash = self.compute_step_hash(step)
            stored_hash = step.get("step_hash")
            
            if computed_hash != stored_hash:
                mismatches.append({
                    "step_index": i,
                    "action": step["action"],
                    "computed_hash": computed_hash,
                    "stored_hash": stored_hash
                })
            
            step_hashes.append(computed_hash)
        
        # Compute commitment hash
        computed_commitment = self.compute_commitment_hash(step_hashes)
        stored_commitment = trace_data.get("commitment_hash")
        
        # Check if commitment hashes match
        is_valid = computed_commitment == stored_commitment and not mismatches
        
        if not is_valid:
            if computed_commitment != stored_commitment:
                logger.error("Commitment hash mismatch!")
                logger.error(f"Computed: {computed_commitment}")
                logger.error(f"Stored:   {stored_commitment}")
        
        return is_valid, mismatches
    
    def load_trace(self, ipfs_hash: Optional[str] = None, file_path: Optional[str] = None) -> Dict:
        """
        Load trace data from IPFS or file.
        
        Args:
            ipfs_hash: IPFS hash (CID) of the trace
            file_path: Path to local trace file
            
        Returns:
            Dict: Trace data
            
        Raises:
            ValueError: If neither ipfs_hash nor file_path is provided
            FileNotFoundError: If file doesn't exist
            Exception: For other loading errors
        """
        if ipfs_hash:
            logger.info(f"Loading trace from IPFS: {ipfs_hash}")
            return self.ipfs_service.download_json(ipfs_hash)
        elif file_path:
            logger.info(f"Loading trace from file: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Trace file not found: {file_path}")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in trace file: {file_path}")
        else:
            raise ValueError("Either ipfs_hash or file_path must be provided")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Verify execution trace integrity")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ipfs-hash", help="IPFS hash (CID) of the trace")
    group.add_argument("--file", help="Path to local trace file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed verification info")
    
    args = parser.parse_args()
    
    try:
        verifier = TraceVerifier()
        trace_data = verifier.load_trace(args.ipfs_hash, args.file)
        
        logger.info("Verifying trace integrity...")
        is_valid, mismatches = verifier.verify_trace(trace_data)
        
        if is_valid:
            logger.info("✅ Trace is valid!")
            if args.verbose:
                logger.info(f"Trace ID: {trace_data['trace_id']}")
                logger.info(f"Agent ID: {trace_data['agent_id']}")
                logger.info(f"Steps: {len(trace_data['steps'])}")
                logger.info(f"Commitment hash: {trace_data['commitment_hash']}")
        else:
            logger.error("❌ Trace is invalid!")
            if mismatches:
                logger.error(f"Found {len(mismatches)} mismatched steps:")
                for mismatch in mismatches:
                    logger.error(f"Step {mismatch['step_index']} ({mismatch['action']}):")
                    logger.error(f"  Computed: {mismatch['computed_hash']}")
                    logger.error(f"  Stored:   {mismatch['stored_hash']}")
        
        return 0 if is_valid else 1
        
    except Exception as e:
        logger.error(f"Error verifying trace: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 