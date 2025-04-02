# NeuroChain

A decentralized system for submitting prompts and generating responses using local LLMs, with on-chain storage and IPFS integration.

## Features

- Submit prompts and receive AI-generated responses
- Store prompts and responses on IPFS
- Record transaction hashes on Base Goerli
- Local LLM inference using TinyLlama
- FastAPI backend with async support

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (optional, for faster inference)
- Base Goerli testnet ETH
- Pinata API credentials

## Installation

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

# IPFS Configuration (Pinata)
PINATA_API_KEY=your_pinata_api_key
PINATA_API_SECRET=your_pinata_api_secret
PINATA_JWT=your_pinata_jwt

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM Configuration
LLM_MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
LLM_MAX_LENGTH=100
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.7
```

## Usage

1. Start the API server:
```bash
uvicorn api.app.main:app --reload
```

2. Submit a prompt:
```bash
curl -X POST http://127.0.0.1:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "user_address": "0x123...abc"
  }'
```

3. Retrieve a prompt:
```bash
curl http://127.0.0.1:8000/prompts/{prompt_id}
```

## Project Structure

```
NeuroChain/
├── api/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── models/
│   │   │   └── prompt.py
│   │   ├── services/
│   │   │   ├── blockchain.py
│   │   │   ├── ipfs.py
│   │   │   └── llm.py
│   │   └── main.py
│   └── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Development

- The project uses FastAPI for the backend
- TinyLlama is used for local LLM inference
- IPFS storage is handled through Pinata
- Base Goerli is used for on-chain storage

## License

MIT License - see LICENSE file for details 