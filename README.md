# NeuroChain

A decentralized system for submitting prompts and generating responses using local LLMs, with on-chain storage and IPFS integration.

## Features

- Submit prompts and receive AI-generated responses
- Store prompts and responses on IPFS
- Record transaction hashes on Base Sepolia
- Local LLM inference using TinyLlama
- FastAPI backend with async support
- Rate limiting and request tracking
- Comprehensive error handling
- Health check endpoint
- CORS support
- IPFS node integration
- Modern React frontend with Chakra UI
- Real-time chat interface
- Blockchain transaction tracking
- IPFS content verification
- MetaMask integration for payments

## Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (optional, for faster inference)
- Base Sepolia testnet ETH
- IPFS node (local or remote)
- MetaMask wallet with Base Sepolia network configured
- Hardhat for smart contract development
- Git for version control

## Installation

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NeuroChain.git
cd NeuroChain
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Node.js dependencies for smart contracts:
```bash
cd contracts
npm install
```

5. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

6. Update the `.env` file with your credentials (see `.env.example` for all required variables)

### Smart Contract Setup

1. Navigate to the contracts directory:
```bash
cd contracts
```

2. Create a `.env` file in the contracts directory:
```env
PRIVATE_KEY=your_private_key_here
BASE_RPC_URL=https://sepolia.base.org
```

3. Compile the contracts:
```bash
npx hardhat compile
```

4. Deploy the contracts to Base Sepolia:

   a. Deploy the Verification contract:
   ```bash
   npx hardhat run scripts/deploy.js --network baseSepolia
   ```
   Copy the deployed Verification contract address and update it in:
   - Backend `.env` file: `CONTRACT_ADDRESS`

   b. Deploy the Payment contract:
   ```bash
   npx hardhat run scripts/deploy_payment.ts --network baseSepolia
   ```
   Copy the deployed Payment contract address and update it in:
   - Backend `.env` file: `PAYMENT_CONTRACT_ADDRESS`
   - Frontend `.env` file: `VITE_PAYMENT_CONTRACT_ADDRESS`

5. Verify the contracts on Base Sepolia:
```bash
# Verify Verification contract
npx hardhat verify --network baseSepolia <verification_contract_address>

# Verify Payment contract
npx hardhat verify --network baseSepolia <payment_contract_address>
```

### IPFS Setup

1. Install IPFS:
```bash
# Using Homebrew (macOS)
brew install ipfs

# Using apt (Ubuntu/Debian)
sudo apt install ipfs

# Using Chocolatey (Windows)
choco install ipfs
```

2. Initialize IPFS:
```bash
ipfs init
```

3. Start the IPFS daemon:
```bash
ipfs daemon
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Create a `.env` file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your contract address:
```env
VITE_PAYMENT_CONTRACT_ADDRESS=your_payment_contract_address_here
```

4. Install dependencies:
```bash
npm install
```

5. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## MetaMask Setup

1. Install MetaMask browser extension if you haven't already
2. Add Base Sepolia network to MetaMask:
   - Network Name: Base Sepolia
   - RPC URL: https://sepolia.base.org
   - Chain ID: 84532
   - Currency Symbol: ETH
   - Block Explorer URL: https://sepolia.basescan.org
3. Get test ETH from the Base Sepolia faucet:
   - Visit https://sepoliafaucet.com/
   - Enter your wallet address
   - Request test ETH
4. Connect your wallet in the NeuroChain interface

## Running the Application

1. Start the IPFS daemon (if using local node):
```bash
ipfs daemon
```

2. Start the backend server:
```bash
cd NeuroChain
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn api.app.main:app --reload
```

3. Start the frontend development server:
```bash
cd frontend
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /models` - Get available models
- `GET /sessions` - Get chat sessions
- `GET /sessions/{session_id}` - Get specific session
- `POST /submit_prompt` - Submit a new prompt
  - Required fields: prompt, model, user_address
  - Optional fields: session_id

## Development

### Backend

- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .`

### Frontend

- Run tests: `npm test`
- Build for production: `npm run build`
- Preview production build: `npm run preview`

### Smart Contracts

- Compile contracts: `npx hardhat compile`
- Run tests: `npx hardhat test`
- Deploy to Base Sepolia: 
  ```bash
  # Deploy Verification contract
  npx hardhat run scripts/deploy_verification.ts --network baseSepolia
  
  # Deploy Payment contract
  npx hardhat run scripts/deploy_payment.ts --network baseSepolia
  ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 