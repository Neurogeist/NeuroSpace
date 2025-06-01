import pytest
import asyncio
from api.app.agents.onchain_qa import OnChainQAAgent

WEB3_PROVIDER = "https://base-mainnet.g.alchemy.com/v2/dZfrIG5r52sQ7UZCgCOmL5z439yCiXlc"
NEUROCOIN_CONTRACT = "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3"

@pytest.fixture
def agent():
    return OnChainQAAgent(agent_id="test-agent", web3_provider=WEB3_PROVIDER)

def test_execute_real_total_supply(agent):
    async def run_test():
        async def mock_parse_question(_: str):
            return {
                "contract_address": NEUROCOIN_CONTRACT,
                "function": "totalSupply",
                "args": [],
                "abi_type": "ERC20"
            }

        agent._parse_question = mock_parse_question

        result = await agent.execute("What is the total supply of NeuroCoin?")
        assert "answer" in result
        assert "trace_id" in result
        assert "ipfs_hash" in result
        assert "commitment_hash" in result
        assert isinstance(result["answer"], str)
        assert "," in result["answer"]
        print("\nFormatted Answer:", result["answer"])

    asyncio.run(run_test())
