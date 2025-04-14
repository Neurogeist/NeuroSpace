const { ethers } = require("hardhat");
require('dotenv').config();

async function main() {
    // Get the contract factory
    const ChatPayment = await ethers.getContractFactory("ChatPayment");
    
    // Deploy the contract
    console.log("Deploying ChatPayment contract...");
    const chatPayment = await ChatPayment.deploy();
    
    // Wait for deployment
    await chatPayment.waitForDeployment();
    
    const address = await chatPayment.getAddress();
    console.log("ChatPayment deployed to:", address);
    
    // Log the contract address to update in .env
    console.log("\nUpdate your .env file with these values:");
    console.log(`PAYMENT_CONTRACT_ADDRESS=${address}`);
    console.log(`REACT_APP_PAYMENT_CONTRACT_ADDRESS=${address}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    }); 