const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  const neuroCoinAddress = "0x298F2AE94754B188DDfd7f8fFd05e40f51D14c60"; // Deployed NeuroCoin
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
