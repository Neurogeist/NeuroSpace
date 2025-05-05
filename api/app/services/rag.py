import logging
import os
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

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

    async def upload_document(self, file_path: str, wallet_address: str) -> Dict[str, Any]:
        """Upload a document to IPFS and store its chunks in the database."""
        try:
            # Read file content
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                try:
                    import PyPDF2
                    text = ""
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                except ImportError:
                    logger.error("PyPDF2 is not installed. Please install it to process PDF files.")
                    raise Exception("PDF processing is not available. Please install PyPDF2.")
            else:
                # For text files
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            # Upload to IPFS
            ipfs_hash = await self.ipfs_service.add_content(text)
            
            # Process document and create chunks
            document_id = str(uuid.uuid4())
            document_name = os.path.basename(file_path)
            
            # Store document upload record
            db = SessionLocal()
            try:
                document_upload = DocumentUpload(
                    document_id=document_id,
                    document_name=document_name,
                    ipfs_hash=ipfs_hash,
                    wallet_address=wallet_address
                )
                db.add(document_upload)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"DB write error: {str(e)}")
                raise
            finally:
                db.close()
            
            # Process document and create chunks
            chunks = self._chunk_text(text)
            
            # Create embeddings for chunks
            embeddings = await self.embed_texts_openai(chunks)
            
            # Store chunks in database
            db = SessionLocal()
            try:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    document_chunk = DocumentChunk(
                        document_id=document_id,
                        document_name=document_name,
                        ipfs_hash=ipfs_hash,
                        chunk_index=i,
                        content=chunk,
                        embedding=embedding
                    )
                    db.add(document_chunk)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"DB write error: {str(e)}")
                raise
            finally:
                db.close()
            
            # Clean up the uploaded file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
            
            return {
                "id": document_id,
                "name": document_name,
                "ipfsHash": ipfs_hash,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            # Clean up the uploaded file in case of error
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
                model_id="mixtral-8x7b-instruct",
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

    async def get_documents(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Get list of uploaded documents for a specific wallet address."""
        try:
            db = SessionLocal()
            try:
                documents = db.query(DocumentUpload).filter(
                    DocumentUpload.wallet_address == wallet_address
                ).all()
                return [{
                    "id": doc.document_id,
                    "name": doc.document_name,
                    "ipfsHash": doc.ipfs_hash,
                    "status": "success"
                } for doc in documents]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            raise

    async def verify_response(self, verification_hash: str, signature: str) -> bool:
        try:
            recovered_address = self.blockchain_service.verify_signature(verification_hash, signature)
            return recovered_address.lower() == self.blockchain_service.account.address.lower()
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            return False
