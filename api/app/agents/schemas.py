"""
Schema definitions for on-chain queries and function metadata.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from web3 import Web3

class FunctionArg(BaseModel):
    """Schema for function arguments."""
    name: str
    type: str
    description: str
    required: bool = True

class FunctionMetadata(BaseModel):
    """Schema for function metadata."""
    name: str
    description: str
    args: List[FunctionArg]
    return_type: str
    return_description: str
    decimals_adjustment: bool = False

class OnChainQuery(BaseModel):
    """Schema for structured on-chain queries."""
    contract_address: str
    function: str
    args: List[Any] = Field(default_factory=list)
    abi_type: str

    @validator('contract_address')
    def validate_contract_address(cls, v: str) -> str:
        """Validate that the contract address is a valid Ethereum address."""
        if not Web3.is_address(v):
            raise ValueError(f"Invalid contract address: {v}")
        return Web3.to_checksum_address(v)

    @validator('abi_type')
    def validate_abi_type(cls, v: str) -> str:
        """Validate that the ABI type is supported."""
        if v not in SUPPORTED_ABI_TYPES:
            raise ValueError(f"Unsupported ABI type: {v}")
        return v

# Supported ABI types
SUPPORTED_ABI_TYPES = {"ERC20"}

# ERC-20 function metadata
ERC20_FUNCTIONS = {
    "totalSupply": FunctionMetadata(
        name="totalSupply",
        description="Get the total supply of tokens",
        args=[],
        return_type="uint256",
        return_description="Total number of tokens in existence",
        decimals_adjustment=True
    ),
    "decimals": FunctionMetadata(
        name="decimals",
        description="Get the number of decimals used for token amounts",
        args=[],
        return_type="uint8",
        return_description="Number of decimals"
    ),
    "symbol": FunctionMetadata(
        name="symbol",
        description="Get the token's symbol",
        args=[],
        return_type="string",
        return_description="Token symbol"
    ),
    "name": FunctionMetadata(
        name="name",
        description="Get the token's name",
        args=[],
        return_type="string",
        return_description="Token name"
    ),
    "balanceOf": FunctionMetadata(
        name="balanceOf",
        description="Get the token balance of an address",
        args=[
            FunctionArg(
                name="owner",
                type="address",
                description="Address to check balance for"
            )
        ],
        return_type="uint256",
        return_description="Token balance",
        decimals_adjustment=True
    ),
    "allowance": FunctionMetadata(
        name="allowance",
        description="Get the amount of tokens approved for spending",
        args=[
            FunctionArg(
                name="owner",
                type="address",
                description="Address that owns the tokens"
            ),
            FunctionArg(
                name="spender",
                type="address",
                description="Address approved to spend the tokens"
            )
        ],
        return_type="uint256",
        return_description="Amount of tokens approved for spending",
        decimals_adjustment=True
    )
}

# System prompt for LLM-based parsing
SYSTEM_PROMPT = """You are a blockchain assistant that converts natural language questions about ERC-20 tokens into structured queries.

Available functions:
{function_descriptions}

Convert the user question into this JSON format:
{{
  "contract_address": "0x...",
  "function": "function_name",
  "args": [],
  "abi_type": "ERC20"
}}

Rules:
1. Only use the functions listed above
2. Always include the contract address
3. Include all required arguments in the args array
4. Only return valid JSON, no comments or text outside the JSON block
5. Never use placeholder addresses (0x...)
""".format(
    function_descriptions="\n".join(
        f"- {name}: {meta.description}" 
        for name, meta in ERC20_FUNCTIONS.items()
    )
) 