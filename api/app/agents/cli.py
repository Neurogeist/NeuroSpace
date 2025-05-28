#!/usr/bin/env python3
"""
Command Line Interface for interacting with NeuroSpace agents.
"""
import asyncio
import argparse
import json
from typing import Optional
import os
from dotenv import load_dotenv

from api.app.agents.onchain_qa import OnChainQAAgent

# Load environment variables
load_dotenv()

async def run_qa_agent(question: str, web3_provider: Optional[str] = None) -> None:
    """
    Run the OnChainQAAgent with the given question.
    
    Args:
        question: The question to ask the agent
        web3_provider: Optional Web3 provider URL. If not provided, uses default from env
    """
    # Use provided web3 provider or default from environment
    provider = web3_provider or os.getenv("WEB3_PROVIDER", "http://localhost:8545")
    
    # Initialize the agent
    agent = OnChainQAAgent(
        agent_id="cli_agent",
        web3_provider=provider
    )
    
    try:
        # Initialize the agent (verify connection)
        await agent.initialize()
        
        # Execute the question
        result = await agent.execute(question)
        
        # Print the answer
        print("\nAnswer:")
        print("-------")
        print(result["answer"])
        
        # Print trace information
        print("\nTrace Information:")
        print("-----------------")
        print(f"Trace ID: {result['trace_id']}")
        print(f"IPFS Hash: {result['ipfs_hash']}")
        print(f"Commitment Hash: {result['commitment_hash']}")
        
        # Print full trace metadata if requested
        if os.getenv("DEBUG", "false").lower() == "true":
            print("\nFull Trace Metadata:")
            print("-------------------")
            print(json.dumps(result["trace_metadata"], indent=2))
            
    except Exception as e:
        print(f"\nError: {str(e)}")

async def interactive_mode(web3_provider: Optional[str] = None):
    """Run the CLI in interactive mode."""
    print("NeuroSpace Agent CLI (Interactive Mode)")
    print("Type 'exit' or 'quit' to end the session")
    print("----------------------------------------")
    
    while True:
        try:
            question = input("\nEnter your question: ").strip()
            if question.lower() in ["exit", "quit"]:
                break
            if question:
                await run_qa_agent(question, web3_provider)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="NeuroSpace Agent CLI - Query on-chain data about tokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example queries:
  - "What is the total supply of USDC?"
  - "What is the balance of 0x1234...5678 for USDT?"
  - "What is the name of the token at 0x1234...5678?"
  - "What is the symbol of the token at 0x1234...5678?"

Common token names: USDC, USDT, DAI, WETH, WBTC
        """
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="The question to ask the agent"
    )
    parser.add_argument(
        "--web3-provider",
        help="Web3 provider URL (defaults to WEB3_PROVIDER env var or http://localhost:8545)"
    )
    
    args = parser.parse_args()
    
    # If no question provided, enter interactive mode
    if not args.question:
        asyncio.run(interactive_mode(args.web3_provider))
    else:
        # Run single question mode
        asyncio.run(run_qa_agent(args.question, args.web3_provider))

if __name__ == "__main__":
    main() 