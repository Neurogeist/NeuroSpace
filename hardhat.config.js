require("@nomicfoundation/hardhat-toolbox");
require('dotenv').config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: "0.8.19",
    networks: {
        baseSepolia: {
            url: process.env.BASE_RPC_URL,
            accounts: [process.env.PRIVATE_KEY],
            chainId: 84532, // Base Sepolia chain ID
        }
    }
};