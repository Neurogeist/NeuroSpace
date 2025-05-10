const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
    const [deployer] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();

    console.log("Deploying ChatPayment contract...");
    console.log(`From address: ${deployer.address}`);
    console.log(`Network: ${network.name} (chainId: ${network.chainId})`);

    const ChatPayment = await ethers.getContractFactory("ChatPayment");
    const chatPayment = await ChatPayment.deploy();

    await chatPayment.waitForDeployment();
    const address = await chatPayment.getAddress();

    console.log("✅ ChatPayment deployed to:", address);

    console.log("\n📌 Update your .env file with:");
    console.log(`PAYMENT_CONTRACT_ADDRESS=${address}`);
    console.log(`REACT_APP_PAYMENT_CONTRACT_ADDRESS=${address}`);
}

main().then(() => process.exit(0)).catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
});
