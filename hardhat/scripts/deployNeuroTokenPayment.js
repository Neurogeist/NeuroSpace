const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  const neuroCoinAddress = "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3"; // Deployed NeuroCoin
  const feeReceiver = deployer.address;

  console.log("🚀 Deploying NeuroTokenPayment with account:", deployer.address);
  console.log("🧠 NeuroCoin address:", neuroCoinAddress);
  console.log("💰 Fee receiver address:", feeReceiver);

  const NeuroTokenPaymentFactory = await hre.ethers.getContractFactory("NeuroTokenPayment");
  const neuroTokenPayment = await NeuroTokenPaymentFactory.deploy(
    neuroCoinAddress,
    feeReceiver
  );

  await neuroTokenPayment.waitForDeployment();
  const paymentAddress = await neuroTokenPayment.getAddress();

  console.log("✅ NeuroTokenPayment deployed to:", paymentAddress);
}

main().catch((error) => {
  console.error("❌ Deployment failed:", error);
  process.exitCode = 1;
});
