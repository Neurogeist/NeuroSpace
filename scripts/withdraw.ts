import { JsonRpcProvider, Wallet, Contract } from "ethers";
import * as dotenv from "dotenv";
dotenv.config();

const CONTRACT_ADDRESS = "0xE76704A7e2057ed6F19CA4E634b91dB91dB03c35";
const ABI = [
  "function withdraw() external",
];

async function main() {
  if (!process.env.PRIVATE_KEY) {
    throw new Error("PRIVATE_KEY not set in .env file");
  }

  const provider = new JsonRpcProvider("https://sepolia.base.org");
  const wallet = new Wallet(process.env.PRIVATE_KEY, provider);
  const contract = new Contract(CONTRACT_ADDRESS, ABI, wallet);

  const tx = await contract.withdraw();
  console.log("Withdraw tx sent:", tx.hash);
  await tx.wait();
  console.log("✅ Withdraw complete.");
}

main().catch((err) => {
  console.error("❌ Error:", err);
});
