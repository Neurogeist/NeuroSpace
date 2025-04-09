const hre = require("hardhat");

async function main() {
  const LLMVerifier = await hre.ethers.getContractFactory("LLMVerifier");
  const contract = await LLMVerifier.deploy();
  await contract.deployed();
  console.log("LLMVerifier deployed to:", contract.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});