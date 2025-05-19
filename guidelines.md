# NeuroSpace – Developer Guidelines

This document outlines key technical conventions, architecture decisions, and development rules for the **NeuroSpace** project. It is designed to help both AI assistants (like Cursor) and human contributors navigate the codebase efficiently.

---

## 🧠 Project Overview

**NeuroSpace** is a decentralized platform for verifiable, auditable AI chat and Retrieval-Augmented Generation (RAG). Users interact with LLMs through a React frontend and FastAPI backend, with verifiability enforced via IPFS and the Base L2 blockchain.

### Core Features

- On-chain cryptographic verification of prompt/response pairs  
- IPFS-backed source storage and metadata  
- Token-gated access via ETH and $NSPACE  
- Wallet-based JWT authentication  
- RAG with traceable document chunks  
- Moderation and feedback system

---

## 🧱 Tech Stack

- **Frontend**: React + Chakra UI (TypeScript)  
- **Backend**: FastAPI (Python 3.13+)  
- **Infrastructure**: Railway (API), Vercel (frontend), Supabase (Postgres)  
- **Blockchain**: Base (L2 Ethereum) via Web3.py  
- **Storage**: IPFS via Pinata  
- **Embeddings**: OpenAI + `pgvector`  
- **Auth**: Wallet-based (eth_account + python-jose)

---

## ⚙️ Architecture Principles

- Every interaction is tied to:
  - a session ID
  - a wallet address
  - model parameters and metadata

- Verification hashes are computed from:
  - prompt  
  - response 
  - metadata (including)
    - model
    - wallet address  
    - session ID  
    - ...

- Uploaded documents go to IPFS, and hashes are logged on-chain  
- Payments are verified via event logs from on-chain contracts

---

## 🔧 Backend Guidelines

- Use **Pydantic models** for all request/response validation  
- JWT auth required on all sensitive routes via `require_jwt_auth`  
- API responses must include:
  - `ipfsHash`
  - `transactionHash`
  - `walletAddress`
  - `model` and other metadata

- All file uploads:
  - Must be validated using `python-magic`
  - Must be scanned for malware

- Supabase is used on dev
- Railway postgres is used on prod

Database looks like
  - `chat_sessions`
  - `chat_messages`
  - `document_chunks`
  - `document_uploads`
  - `flagged_messages`
  - `free_requests`

---

## 💻 Frontend Guidelines

- Follow **camelCase** conventions in props and variables  
- Each message should show:
  - Model metadata (`model`, `temperature`, `systemPrompt`)
  - Verification status (e.g., hash match, signature verified)
  - IPFS and BaseScan links (if available)

- JWTs are stored securely in memory or via HTTP-only cookies   
- Session state is cached using `localStorage`

---

## 🔐 Security Guidelines

- Secrets are managed via environment variables only — no hardcoding  
- Hash verification must always be recomputed from raw data  
- JWTs should be short-lived and signed using strong keys  
- Inputs must be sanitized and validated at upload and inference
- Redis is used for rate limiting and distributed lock

---

Tokenomics: NeuroCoin (NSPACE)
Token Symbol: NSPACE

- Max Supply: 100,000,000
- Payments: ETH and NSPACE supported
- Verification: Logs from NeuroTokenPayment contract used to validate payment
- Future uses: staking, governance, ecosystem rewards

---

LLM Behavior

- Supports multiple model providers (OpenAI, Together, etc.)
- Local inference is deprecated in favor of managed APIs
- Prompt generation uses full session history and token-aware truncation

---

🧪 Testing and Tooling

- Use pytest for backend testing with httpx.AsyncClient for async routes

Test coverage should include:

- Signature verification
- JWT flows
- Prompt/response hashing
- Payment verification

Add a Makefile with tasks for:

- make test – run tests
- make lint – lint codebase
- make deploy – deploy backend/frontend

