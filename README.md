# NeuroChain

A decentralized system for submitting prompts and generating responses using local LLMs, with on-chain storage and IPFS integration.

## Features

- Submit prompts and receive AI-generated responses
- Store prompts and responses on IPFS
- Record transaction hashes on Base Goerli
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

## Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (optional, for faster inference)
- Base Goerli testnet ETH
- IPFS node (local or remote)
- Base Goerli testnet ETH

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

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your credentials:
```env
# Base Chain Configuration
BASE_RPC_URL=https://goerli.base.org
PRIVATE_KEY=your_private_key_here

# IPFS Configuration
IPFS_API_URL=http://localhost:5001/api/v0  # Local IPFS node
# Or use a remote IPFS node:
# IPFS_API_URL=https://ipfs.infura.io:5001/api/v0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # 1 hour in seconds

# LLM Configuration
LLM_MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
LLM_MAX_LENGTH=100
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.7
```

5. Start IPFS node (if using local node):
```bash
ipfs daemon
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

### Backend API

1. Start the API server:
```bash
uvicorn api.app.main:app --reload
```

2. Submit a prompt:
```bash
curl -X POST http://127.0.0.1:8000/prompts \
  -H "Content-Type: application/json" \
  -H "X-User-Address: 0x1234567890123456789012345678901234567890" \
  -d '{
    "prompt": "What is the capital of France?"
  }'
```

3. Check API health:
```bash
curl http://127.0.0.1:8000/health
```

### Frontend Interface

1. Open your browser and navigate to `http://localhost:5173`
2. Enter your prompt in the chat interface
3. View the response, IPFS hash, and blockchain transaction details
4. Use the clear button to reset the chat history

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /prompts` - Submit a new prompt
  - Required headers: `X-User-Address`
  - Response includes:
    - Generated response
    - IPFS CID
    - Blockchain transaction signature
    - Timestamp
    - User address

## Development

### Backend

- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .`

### Frontend

- Run tests: `npm test`
- Build for production: `npm run build`
- Preview production build: `npm run preview`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 