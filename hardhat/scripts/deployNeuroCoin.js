const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying NeuroCoin with account:", deployer.address);

  const NeuroCoinFactory = await hre.ethers.getContractFactory("NeuroCoin");
  const neuroCoin = await NeuroCoinFactory.deploy();

  await neuroCoin.waitForDeployment();

  const contractAddress = await neuroCoin.getAddress();
  console.log("NeuroCoin deployed to:", contractAddress);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});