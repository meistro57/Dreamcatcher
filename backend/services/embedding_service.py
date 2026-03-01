"""
Embedding Service for Semantic Search
Handles vector embeddings for idea content using sentence-transformers
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime

try:  # pragma: no cover - optional dependency
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover
    cosine_similarity = None

try:  # pragma: no cover - optional heavy dependency
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None

try:  # pragma: no cover - optional GPU dependency
    import torch
except ImportError:  # pragma: no cover
    torch = None

try:  # pragma: no cover
    from ..database.models import Idea, AgentLog
    from ..database.database import SessionLocal
except ImportError:  # pragma: no cover
    from database.models import Idea, AgentLog
    from database.database import SessionLocal

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing text embeddings for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if SentenceTransformer is None:
            logger.warning(
                "sentence-transformers is not installed; semantic embeddings will use mocks in tests"
            )
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of float values representing the embedding
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.model.encode, 
                text
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings batch: {e}")
            raise
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1).reshape(1, -1)
            emb2 = np.array(embedding2).reshape(1, -1)
            
            # Calculate cosine similarity
            if cosine_similarity is not None:
                similarity = cosine_similarity(emb1, emb2)[0][0]
            else:
                norm_product = np.linalg.norm(emb1) * np.linalg.norm(emb2)
                if norm_product == 0:
                    return 0.0
                similarity = float(np.dot(emb1, emb2.T) / norm_product)
            
            # Convert to 0-1 range (cosine similarity is -1 to 1)
            return (similarity + 1) / 2
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def update_idea_embedding(self, idea_id: str, content: str) -> bool:
        """
        Update embedding for a specific idea
        
        Args:
            idea_id: ID of the idea to update
            content: Content to generate embedding for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Update in database
            db = SessionLocal()
            try:
                idea = db.query(Idea).filter(Idea.id == idea_id).first()
                if idea:
                    idea.content_embedding = embedding
                    idea.embedding_model = self.model_name
                    idea.embedding_updated_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Updated embedding for idea {idea_id}")
                    return True
                else:
                    logger.warning(f"Idea {idea_id} not found")
                    return False
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to update idea embedding: {e}")
            return False
    
    async def search_similar_ideas(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for ideas similar to a query
        
        Args:
            query: Search query
            user_id: User ID to search within
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar ideas with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            # Search in database using PostgreSQL vector operations
            db = SessionLocal()
            try:
                # Use raw SQL for vector similarity search
                sql = text("""
                    SELECT 
                        i.id,
                        i.content_processed,
                        i.content_transcribed,
                        i.content_raw,
                        i.category,
                        i.urgency_score,
                        i.novelty_score,
                        i.viability_score,
                        i.created_at,
                        i.is_favorite,
                        i.is_archived,
                        i.content_embedding,
                        CASE 
                            WHEN i.content_embedding IS NULL THEN 0
                            ELSE (1 + (
                                SELECT 
                                    (array_to_vector(i.content_embedding) <=> array_to_vector(:query_embedding))
                            )) / 2
                        END as similarity_score
                    FROM ideas i
                    WHERE i.user_id = :user_id 
                        AND i.is_archived = false
                        AND i.content_embedding IS NOT NULL
                    ORDER BY similarity_score DESC
                    LIMIT :limit
                """)
                
                result = db.execute(sql, {
                    'query_embedding': query_embedding,
                    'user_id': user_id,
                    'limit': limit
                }).fetchall()
                
                # Convert to list of dictionaries
                ideas = []
                for row in result:
                    # Calculate similarity manually if needed
                    similarity = row.similarity_score
                    if row.content_embedding and similarity >= threshold:
                        ideas.append({
                            'id': row.id,
                            'content_processed': row.content_processed,
                            'content_transcribed': row.content_transcribed,
                            'content_raw': row.content_raw,
                            'category': row.category,
                            'urgency_score': row.urgency_score,
                            'novelty_score': row.novelty_score,
                            'viability_score': row.viability_score,
                            'created_at': row.created_at,
                            'is_favorite': row.is_favorite,
                            'is_archived': row.is_archived,
                            'similarity_score': similarity
                        })
                
                return ideas
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to search similar ideas: {e}")
            return []
    
    async def find_related_ideas(
        self, 
        idea_id: str, 
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find ideas related to a specific idea
        
        Args:
            idea_id: ID of the idea to find related ideas for
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of related ideas with similarity scores
        """
        try:
            # Get the idea and its embedding
            db = SessionLocal()
            try:
                idea = db.query(Idea).filter(Idea.id == idea_id).first()
                if not idea or not idea.content_embedding:
                    return []
                
                # Get the content for search
                content = idea.content_processed or idea.content_transcribed or idea.content_raw
                
                # Search for similar ideas
                return await self.search_similar_ideas(
                    content, 
                    idea.user_id, 
                    limit + 1,  # +1 because we'll filter out the original idea
                    threshold
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to find related ideas: {e}")
            return []
    
    async def batch_update_embeddings(self, batch_size: int = 50) -> int:
        """
        Update embeddings for all ideas that don't have them
        
        Args:
            batch_size: Number of ideas to process at once
            
        Returns:
            Number of embeddings updated
        """
        updated_count = 0
        
        try:
            db = SessionLocal()
            try:
                # Get ideas without embeddings
                ideas = db.query(Idea).filter(
                    Idea.content_embedding.is_(None),
                    Idea.is_archived == False
                ).limit(batch_size).all()
                
                if not ideas:
                    logger.info("No ideas need embedding updates")
                    return 0
                
                # Prepare content for batch processing
                contents = []
                for idea in ideas:
                    content = idea.content_processed or idea.content_transcribed or idea.content_raw
                    contents.append(content)
                
                # Generate embeddings in batch
                embeddings = await self.generate_embeddings_batch(contents)
                
                # Update database
                for idea, embedding in zip(ideas, embeddings):
                    idea.content_embedding = embedding
                    idea.embedding_model = self.model_name
                    idea.embedding_updated_at = datetime.utcnow()
                    updated_count += 1
                
                db.commit()
                logger.info(f"Updated {updated_count} embeddings")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to batch update embeddings: {e}")
        
        return updated_count
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings in the database
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            db = SessionLocal()
            try:
                # Count total ideas
                total_ideas = db.query(Idea).filter(Idea.is_archived == False).count()
                
                # Count ideas with embeddings
                ideas_with_embeddings = db.query(Idea).filter(
                    Idea.content_embedding.isnot(None),
                    Idea.is_archived == False
                ).count()
                
                # Count by model
                model_stats = db.query(
                    Idea.embedding_model,
                    db.func.count(Idea.id)
                ).filter(
                    Idea.content_embedding.isnot(None),
                    Idea.is_archived == False
                ).group_by(Idea.embedding_model).all()
                
                return {
                    'total_ideas': total_ideas,
                    'ideas_with_embeddings': ideas_with_embeddings,
                    'coverage_percentage': (ideas_with_embeddings / total_ideas * 100) if total_ideas > 0 else 0,
                    'model_stats': dict(model_stats),
                    'current_model': self.model_name,
                    'embedding_dimension': self.dimension
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {}

    def build_log_embedding_text(self, log: AgentLog) -> str:
        """
        Build searchable text for an agent log embedding.

        Args:
            log: AgentLog instance

        Returns:
            Normalized text payload
        """
        parts = [
            f"agent:{log.agent_id}",
            f"action:{log.action}",
            f"status:{log.status}",
        ]

        if log.error_message:
            parts.append(f"error:{log.error_message}")

        if log.idea_id:
            parts.append(f"idea:{log.idea_id}")

        if log.input_data:
            try:
                parts.append(f"input:{json.dumps(log.input_data, sort_keys=True, default=str)}")
            except Exception:
                parts.append(f"input:{str(log.input_data)}")

        if log.output_data:
            try:
                parts.append(f"output:{json.dumps(log.output_data, sort_keys=True, default=str)}")
            except Exception:
                parts.append(f"output:{str(log.output_data)}")

        return "\n".join(parts)

    async def update_log_embedding(self, log_id: str) -> bool:
        """
        Generate and persist embedding for a single agent log.

        Args:
            log_id: AgentLog id

        Returns:
            True on success, False otherwise
        """
        db = SessionLocal()
        try:
            log = db.query(AgentLog).filter(AgentLog.id == log_id).first()
            if not log:
                logger.warning(f"Agent log {log_id} not found")
                return False

            text_payload = self.build_log_embedding_text(log)
            if not text_payload.strip():
                logger.warning(f"Agent log {log_id} has no searchable payload")
                return False

            embedding = await self.generate_embedding(text_payload)

            log.content_embedding = embedding
            log.embedding_model = self.model_name
            log.embedding_updated_at = datetime.utcnow()
            db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to update log embedding for {log_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def batch_update_log_embeddings(self, batch_size: int = 100) -> int:
        """
        Generate embeddings for logs missing embeddings.

        Args:
            batch_size: Maximum logs per run

        Returns:
            Number of updated rows
        """
        updated_count = 0
        db = SessionLocal()
        try:
            logs = db.query(AgentLog).filter(
                AgentLog.content_embedding.is_(None)
            ).order_by(AgentLog.started_at.desc()).limit(batch_size).all()

            if not logs:
                return 0

            payloads = [self.build_log_embedding_text(log) for log in logs]
            embeddings = await self.generate_embeddings_batch(payloads)

            for log, embedding in zip(logs, embeddings):
                log.content_embedding = embedding
                log.embedding_model = self.model_name
                log.embedding_updated_at = datetime.utcnow()
                updated_count += 1

            db.commit()
            return updated_count
        except Exception as e:
            logger.error(f"Failed to batch update log embeddings: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    async def search_similar_logs(
        self,
        query: str,
        limit: int = 20,
        threshold: float = 0.4,
        agent_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search similar logs using cosine similarity.

        Args:
            query: User search text
            limit: Max results
            threshold: Min similarity threshold
            agent_id: Optional agent filter
            status: Optional status filter

        Returns:
            Similar log list with scores
        """
        db = SessionLocal()
        try:
            query_embedding = await self.generate_embedding(query)

            db_query = db.query(AgentLog).filter(AgentLog.content_embedding.isnot(None))
            if agent_id:
                db_query = db_query.filter(AgentLog.agent_id == agent_id)
            if status:
                db_query = db_query.filter(AgentLog.status == status)

            # Cap candidate size to keep latency bounded.
            candidates = db_query.order_by(AgentLog.started_at.desc()).limit(1000).all()

            scored_results = []
            for log in candidates:
                if not log.content_embedding:
                    continue

                similarity = self.calculate_similarity(query_embedding, log.content_embedding)
                if similarity < threshold:
                    continue

                scored_results.append({
                    "id": log.id,
                    "agent_id": log.agent_id,
                    "idea_id": log.idea_id,
                    "action": log.action,
                    "status": log.status,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "error_message": log.error_message,
                    "input_data": log.input_data,
                    "output_data": log.output_data,
                    "similarity_score": similarity
                })

            scored_results.sort(key=lambda row: row["similarity_score"], reverse=True)
            return scored_results[:limit]
        except Exception as e:
            logger.error(f"Failed to search similar logs: {e}")
            return []
        finally:
            db.close()

    async def get_log_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding coverage stats for agent logs."""
        db = SessionLocal()
        try:
            total_logs = db.query(AgentLog).count()
            logs_with_embeddings = db.query(AgentLog).filter(
                AgentLog.content_embedding.isnot(None)
            ).count()

            model_stats = db.query(
                AgentLog.embedding_model,
                db.func.count(AgentLog.id)
            ).filter(
                AgentLog.content_embedding.isnot(None)
            ).group_by(AgentLog.embedding_model).all()

            return {
                "total_logs": total_logs,
                "logs_with_embeddings": logs_with_embeddings,
                "coverage_percentage": (logs_with_embeddings / total_logs * 100) if total_logs > 0 else 0,
                "model_stats": dict(model_stats),
                "current_model": self.model_name,
                "embedding_dimension": self.dimension
            }
        except Exception as e:
            logger.error(f"Failed to get log embedding stats: {e}")
            return {}
        finally:
            db.close()

# Global instance
embedding_service = EmbeddingService()
