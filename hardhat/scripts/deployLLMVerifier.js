const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = await hre.ethers.provider.getNetwork();

  console.log(`Deploying LLMVerifier from ${deployer.address}`);
  console.log(`Network: ${network.name} (chainId: ${network.chainId})`);

  const LLMVerifier = await hre.ethers.getContractFactory("LLMVerifier");
  const contract = await LLMVerifier.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`✅ LLMVerifier deployed to: ${address}`);

  console.log("\n📌 Update your .env file with:");
  console.log(`CONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error("❌ Deployment failed:", error);
  process.exit(1);
});
