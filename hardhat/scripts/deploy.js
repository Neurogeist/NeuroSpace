const hre = require("hardhat");

async function main() {
  const LLMVerifier = await hre.ethers.getContractFactory("LLMVerifier");
  const contract = await LLMVerifier.deploy();
  await contract.waitForDeployment();
  console.log("LLMVerifier deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});