"""
Schema definitions for on-chain queries and function metadata.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from web3 import Web3

# Token registry mapping names to contract addresses
TOKEN_REGISTRY = {
    "neurocoin": "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3",
    "neuro": "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3",  # aliases
    "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base USDC
    "usd coin": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "weth": "0x4200000000000000000000000000000000000006",  # Base WETH
    "wrapped eth": "0x4200000000000000000000000000000000000006",
    "wrapped ether": "0x4200000000000000000000000000000000000006",
}

class FunctionArg(BaseModel):
    """Schema for function arguments."""
    name: str
    type: str
    description: str
    required: bool = True
    example: Optional[str] = None

class FunctionMetadata(BaseModel):
    """Schema for function metadata."""
    name: str
    description: str
    args: List[FunctionArg]
    return_type: str
    return_description: str
    decimals_adjustment: bool = False
    example_question: str

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

    @classmethod
    def resolve_token_name(cls, token_name: str) -> Optional[str]:
        """
        Resolve a token name to its contract address.
        
        Args:
            token_name: The token name to resolve
            
        Returns:
            Optional[str]: The contract address if found, None otherwise
        """
        token_name = token_name.lower().strip()
        return TOKEN_REGISTRY.get(token_name)

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
        decimals_adjustment=True,
        example_question="What is the total supply of USDC?"
    ),
    "decimals": FunctionMetadata(
        name="decimals",
        description="Get the number of decimals used for token amounts",
        args=[],
        return_type="uint8",
        return_description="Number of decimals",
        example_question="How many decimals does USDC have?"
    ),
    "symbol": FunctionMetadata(
        name="symbol",
        description="Get the token's symbol",
        args=[],
        return_type="string",
        return_description="Token symbol",
        example_question="What is the symbol of USDC?"
    ),
    "name": FunctionMetadata(
        name="name",
        description="Get the token's name",
        args=[],
        return_type="string",
        return_description="Token name",
        example_question="What is the full name of USDC?"
    ),
    "balanceOf": FunctionMetadata(
        name="balanceOf",
        description="Get the token balance of an address",
        args=[
            FunctionArg(
                name="owner",
                type="address",
                description="Address to check balance for",
                example="0x1234567890123456789012345678901234567890"
            )
        ],
        return_type="uint256",
        return_description="Token balance",
        decimals_adjustment=True,
        example_question="What is the USDC balance of 0x123...?"
    ),
    "allowance": FunctionMetadata(
        name="allowance",
        description="Get the amount of tokens approved for spending",
        args=[
            FunctionArg(
                name="owner",
                type="address",
                description="Address that owns the tokens",
                example="0x1234567890123456789012345678901234567890"
            ),
            FunctionArg(
                name="spender",
                type="address",
                description="Address approved to spend the tokens",
                example="0x0987654321098765432109876543210987654321"
            )
        ],
        return_type="uint256",
        return_description="Amount of tokens approved for spending",
        decimals_adjustment=True,
        example_question="What is the USDC allowance of 0x123... for 0x456...?"
    )
}

# System prompt for LLM-based parsing
SYSTEM_PROMPT = """You are a blockchain assistant that converts natural language questions about ERC-20 tokens into structured queries.

Available functions:
{function_descriptions}

Known tokens and their addresses:
{token_descriptions}

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format:
{{
  "contract_address": "0x...",
  "function": "function_name",
  "args": [],
  "abi_type": "ERC20"
}}

Rules:
1. Only use the functions listed above
2. For known tokens (USDC, WETH, etc.), ALWAYS use their exact contract addresses from the list above
3. For unknown tokens, you must be given a valid contract address in the question
4. Include all required arguments in the args array
5. ONLY return the JSON object, no other text or comments
6. NEVER use placeholder addresses (0x...)
7. If an address is mentioned, validate it's a proper Ethereum address

Example questions and answers:
Q: What is the total supply of USDC?
A: {{"contract_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "function": "totalSupply", "args": [], "abi_type": "ERC20"}}

Q: What is the balance of 0x1234567890123456789012345678901234567890?
A: {{"contract_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "function": "balanceOf", "args": ["0x1234567890123456789012345678901234567890"], "abi_type": "ERC20"}}

Q: How many decimals does WETH have?
A: {{"contract_address": "0x4200000000000000000000000000000000000006", "function": "decimals", "args": [], "abi_type": "ERC20"}}

Q: What is the symbol of neurocoin?
A: {{"contract_address": "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3", "function": "symbol", "args": [], "abi_type": "ERC20"}}

IMPORTANT: When a token name is mentioned (like USDC, WETH, etc.), you MUST use its exact contract address from the list above. Never use placeholder addresses.
""".format(
    function_descriptions="\n".join(
        f"- {name}: {meta.description}" 
        for name, meta in ERC20_FUNCTIONS.items()
    ),
    token_descriptions="\n".join(
        f"- {name}: {addr}" 
        for name, addr in TOKEN_REGISTRY.items()
    )
) 