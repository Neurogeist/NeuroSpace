import logging
import os
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

import openai
import numpy as np
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from ..models.document import DocumentChunk, DocumentUpload
from ..models.database import SessionLocal
from .llm import LLMService
from .blockchain import BlockchainService
from .ipfs import IPFSService
from .chat_session import ChatSessionService

openai.api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        llm_service: LLMService,
        blockchain_service: BlockchainService,
        ipfs_service: IPFSService,
        chat_session_service: ChatSessionService
    ):
        self.llm_service = llm_service
        self.blockchain_service = blockchain_service
        self.ipfs_service = ipfs_service
        self.chat_session_service = chat_session_service
        self.chunk_size = 1000
        self.chunk_overlap = 100
        self.embedding_dim = 1536  # for OpenAI ada-002

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        try:
            logger.info(f"Starting text chunking. Text length: {len(text)}")
            chunks = []
            start = 0
            
            # Split text into paragraphs first
            paragraphs = text.split('\n\n')
            logger.info(f"Split into {len(paragraphs)} paragraphs")
            
            current_chunk = ""
            for paragraph in paragraphs:
                # If adding this paragraph would exceed chunk size, save current chunk
                if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n"
                    current_chunk += paragraph
            
            # Add the last chunk if it exists
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            logger.info(f"Completed chunking. Total chunks: {len(chunks)}")
            return chunks
        except Exception as e:
            logger.error(f"Error in _chunk_text: {str(e)}")
            raise

    async def embed_texts_openai(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI's API."""
        try:
            from openai import OpenAI
            client = OpenAI()
            
            # Process in batches to avoid rate limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing embedding batch {i//batch_size + 1}")
                
                response = await run_in_threadpool(
                    lambda: client.embeddings.create(
                        input=batch,
                        model="text-embedding-ada-002"
                    )
                )
                
                batch_embeddings = [d.embedding for d in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Error in embed_texts_openai: {str(e)}")
            raise

    async def upload_document(self, file_path: str) -> Dict[str, Any]:
        try:
            logger.info("Reading document file")
            with open(file_path, "rb") as f:
                content_bytes = f.read()
            content = content_bytes.decode("utf-8")
            logger.info(f"Read {len(content)} characters from file")

            logger.info("Uploading to IPFS")
            ipfs_hash = await self.ipfs_service.add_content(content)
            logger.info(f"Uploaded to IPFS: {ipfs_hash}")

            document_id = hashlib.sha256(file_path.encode()).hexdigest()
            document_name = Path(file_path).name

            logger.info("Processing document into chunks")
            chunks = self._chunk_text(content)
            logger.info(f"Created {len(chunks)} chunks from document")

            logger.info("Starting OpenAI embedding")
            try:
                chunk_embeddings = await self.embed_texts_openai(chunks)
                logger.info(f"Successfully created embeddings for {len(chunk_embeddings)} chunks")
            except Exception as e:
                logger.error(f"Error during OpenAI embedding: {str(e)}")
                raise

            logger.info("Starting database operations")
            db = SessionLocal()
            try:
                upload = DocumentUpload(
                    document_id=document_id,
                    name=document_name,
                    ipfs_hash=ipfs_hash
                )
                db.add(upload)
                logger.info("Added document upload record")

                for i, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
                    chunk_record = DocumentChunk(
                        document_id=document_id,
                        document_name=document_name,
                        ipfs_hash=ipfs_hash,
                        chunk_index=i,
                        content=chunk,
                        embedding=emb
                    )
                    db.add(chunk_record)
                logger.info(f"Added {len(chunks)} chunk records")

                db.commit()
                logger.info("Successfully committed database changes")
            except Exception as e:
                db.rollback()
                logger.error(f"DB write error: {str(e)}")
                raise
            finally:
                db.close()
                logger.info("Closed database connection")

            os.remove(file_path)
            logger.info("Cleaned up temporary file")

            return {
                "id": document_id,
                "name": document_name,
                "ipfsHash": ipfs_hash,
                "status": "Uploaded",
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            try:
                os.remove(file_path)
            except:
                pass
            raise

    async def query_documents(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            logger.info("Embedding query")
            query_embedding = await self.embed_texts_openai([query])
            query_vec = query_embedding[0]
            logger.info(f"Query vector length: {len(query_vec)}")

            logger.info("Running similarity query")
            sql = text("""
                SELECT *,
                    1 - (embedding <#> (:query_vector)::vector) AS similarity
                FROM document_chunks
                ORDER BY embedding <#> (:query_vector)::vector
                LIMIT :top_k
            """)
            result = db.execute(sql, {"query_vector": query_vec, "top_k": top_k}).mappings().fetchall()

            if not result:
                return {
                    "response": "I couldn't find relevant information in the uploaded documents.",
                    "sources": [],
                    "verification_hash": "",
                    "signature": "",
                    "transaction_hash": "",
                    "ipfs_cid": ""
                }

            chunks = [{
                "document_id": r["document_id"],
                "document_name": r["document_name"],
                "ipfsHash": r["ipfs_hash"],
                "chunk_index": r["chunk_index"],
                "content": r["content"],
                "similarity": r["similarity"]
            } for r in result]

            context = "\n\n".join([
                f"Document: {c['document_name']}\nContent: {c['content']}" for c in chunks
            ])

            prompt = f"""Based on the following context, answer the question below.
If the answer cannot be found in the context, say "I cannot find the answer in the provided documents."

Context:
{context}

Question: {query}

Answer:"""

            llm_response = await self.llm_service.generate_response(
                model_id="gpt-3.5-turbo",
                prompt=prompt,
                temperature=0.7
            )
            response = llm_response.get("response", "") if isinstance(llm_response, dict) else llm_response

            timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            sources = [{
                "id": c["document_id"],
                "snippet": c["content"],
                "ipfsHash": c["ipfsHash"],
                "chunk_index": c["chunk_index"],
                "similarity": c["similarity"]
            } for c in chunks]

            payload = {
                "query": query,
                "response": response,
                "sources": sources,
                "timestamp": timestamp
            }

            verification_hash = self.llm_service.create_verification_hash(payload)
            signature = self.blockchain_service.sign_message(verification_hash)
            blockchain_result = await self.blockchain_service.submit_to_blockchain(verification_hash)
            transaction_hash = blockchain_result.get("transaction_hash")

            ipfs_data = {
                **payload,
                "verification_hash": verification_hash,
                "signature": signature,
                "transaction_hash": transaction_hash
            }
            ipfs_cid = await self.ipfs_service.upload_json(ipfs_data)

            return {
                "response": response,
                "sources": sources,
                "verification_hash": verification_hash,
                "signature": signature,
                "transaction_hash": transaction_hash,
                "ipfs_cid": ipfs_cid
            }

        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise
        finally:
            db.close()

    async def get_documents(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            uploads = db.query(DocumentUpload).all()
            return [
                {
                    "id": u.document_id,
                    "name": u.name,
                    "ipfsHash": u.ipfs_hash,
                    "uploaded_at": u.uploaded_at.isoformat()
                }
                for u in uploads
            ]
        finally:
            db.close()

    async def verify_response(self, verification_hash: str, signature: str) -> bool:
        try:
            result = await self.blockchain_service.verify_message(verification_hash, signature)
            return result.get("verified", False)
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            return False
