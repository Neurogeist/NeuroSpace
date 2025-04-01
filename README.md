# NeuroChain: Verifiable LLM Inference on Solana

A proof-of-concept for running LLM inference on-chain with Solana smart contracts and off-chain Python services.

## Project Structure

```
.
├── program/                 # Solana smart contract (Rust)
│   ├── src/
│   └── Cargo.toml
├── api/                    # Python FastAPI service
│   ├── app/
│   ├── requirements.txt
│   └── Dockerfile
└── tests/                  # Integration tests
```

## Features

- Solana smart contract for prompt submission and response storage
- Off-chain Python service for LLM inference
- FastAPI REST API for monitoring and testing
- Integration with HuggingFace Transformers for model inference

## Prerequisites

- Rust and Solana CLI tools
- Python 3.9+
- Docker (optional)

## Setup Instructions

### 1. Deploy Smart Contract

```bash
# Build the program
cd program
cargo build-bpf

# Deploy to localnet
solana program deploy target/deploy/neurochain.so --url localhost
```

### 2. Run Python Service

```bash
# Create virtual environment
cd api
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload
```

### 3. Test the Flow

1. Submit a prompt using the API:
```bash
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

2. Monitor the response:
```bash
curl http://localhost:8000/prompts/{prompt_id}
```

## Future Enhancements

- [ ] Add verifiable inference proofs
- [ ] Implement ZK proofs for model outputs
- [ ] Support multiple LLM models
- [ ] Add model performance metrics
- [ ] Implement batch processing
- [ ] Add rate limiting and access control

## Development

### Local Development

1. Start local Solana validator:
```bash
solana-test-validator
```

2. Deploy program to localnet
3. Run Python service
4. Use test scripts to verify functionality

### Testing

```bash
# Run integration tests
cd tests
python -m pytest
```

## License

MIT 