"""
Semantic Agent - Handles semantic search and content understanding
Generates embeddings, finds similar ideas, and enhances search capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..services.embedding_service import embedding_service
from ..database.models import Idea, AgentLog
from ..database.database import SessionLocal

logger = logging.getLogger(__name__)

class SemanticAgent(BaseAgent):
    """Agent responsible for semantic understanding and search capabilities"""
    
    def __init__(self):
        super().__init__(
            agent_id="semantic",
            name="Semantic Agent",
            description="Handles semantic search and content understanding",
            version="1.0.0"
        )
        self.embedding_service = embedding_service
        
    async def process_idea(self, idea_id: str) -> Dict[str, Any]:
        """
        Process an idea for semantic understanding
        
        Args:
            idea_id: ID of the idea to process
            
        Returns:
            Processing result with embedding info
        """
        try:
            # Get idea from database
            db = SessionLocal()
            try:
                idea = db.query(Idea).filter(Idea.id == idea_id).first()
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Get content for embedding
                content = idea.content_processed or idea.content_transcribed or idea.content_raw
                if not content:
                    return {"success": False, "error": "No content to process"}
                
                # Log processing start
                await self.log_activity(
                    idea_id=idea_id,
                    action="generate_embedding",
                    status="started",
                    input_data={"content_length": len(content)}
                )
                
                # Generate embedding
                success = await self.embedding_service.update_idea_embedding(idea_id, content)
                
                if success:
                    # Find related ideas
                    related_ideas = await self.embedding_service.find_related_ideas(
                        idea_id=idea_id,
                        limit=5,
                        threshold=0.6
                    )
                    
                    # Log success
                    await self.log_activity(
                        idea_id=idea_id,
                        action="generate_embedding",
                        status="completed",
                        output_data={
                            "embedding_generated": True,
                            "related_ideas_found": len(related_ideas)
                        }
                    )
                    
                    return {
                        "success": True,
                        "embedding_generated": True,
                        "related_ideas": related_ideas,
                        "message": "Semantic processing completed successfully"
                    }
                else:
                    # Log failure
                    await self.log_activity(
                        idea_id=idea_id,
                        action="generate_embedding",
                        status="failed",
                        error_message="Failed to generate embedding"
                    )
                    
                    return {
                        "success": False,
                        "error": "Failed to generate embedding"
                    }
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing idea {idea_id}: {e}")
            await self.log_activity(
                idea_id=idea_id,
                action="generate_embedding",
                status="failed",
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def search_similar_ideas(self, query: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Search for ideas similar to a query
        
        Args:
            query: Search query
            user_id: User ID to search within
            **kwargs: Additional search parameters
            
        Returns:
            Search results with similarity scores
        """
        try:
            # Extract parameters
            limit = kwargs.get('limit', 10)
            threshold = kwargs.get('threshold', 0.5)
            
            # Log search start
            await self.log_activity(
                action="semantic_search",
                status="started",
                input_data={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit,
                    "threshold": threshold
                }
            )
            
            # Perform search
            similar_ideas = await self.embedding_service.search_similar_ideas(
                query=query,
                user_id=user_id,
                limit=limit,
                threshold=threshold
            )
            
            # Log success
            await self.log_activity(
                action="semantic_search",
                status="completed",
                output_data={
                    "results_found": len(similar_ideas),
                    "query": query
                }
            )
            
            return {
                "success": True,
                "results": similar_ideas,
                "query": query,
                "total_results": len(similar_ideas)
            }
            
        except Exception as e:
            logger.error(f"Error searching similar ideas: {e}")
            await self.log_activity(
                action="semantic_search",
                status="failed",
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def find_related_ideas(self, idea_id: str, **kwargs) -> Dict[str, Any]:
        """
        Find ideas related to a specific idea
        
        Args:
            idea_id: ID of the source idea
            **kwargs: Additional parameters
            
        Returns:
            Related ideas with similarity scores
        """
        try:
            # Extract parameters
            limit = kwargs.get('limit', 5)
            threshold = kwargs.get('threshold', 0.6)
            
            # Log search start
            await self.log_activity(
                idea_id=idea_id,
                action="find_related",
                status="started",
                input_data={
                    "limit": limit,
                    "threshold": threshold
                }
            )
            
            # Find related ideas
            related_ideas = await self.embedding_service.find_related_ideas(
                idea_id=idea_id,
                limit=limit,
                threshold=threshold
            )
            
            # Filter out the original idea
            related_ideas = [idea for idea in related_ideas if idea['id'] != idea_id]
            
            # Log success
            await self.log_activity(
                idea_id=idea_id,
                action="find_related",
                status="completed",
                output_data={
                    "related_ideas_found": len(related_ideas)
                }
            )
            
            return {
                "success": True,
                "related_ideas": related_ideas,
                "total_found": len(related_ideas)
            }
            
        except Exception as e:
            logger.error(f"Error finding related ideas: {e}")
            await self.log_activity(
                idea_id=idea_id,
                action="find_related",
                status="failed",
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def batch_update_embeddings(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Update embeddings for ideas that don't have them
        
        Args:
            batch_size: Number of ideas to process at once
            
        Returns:
            Update results
        """
        try:
            # Log batch update start
            await self.log_activity(
                action="batch_update_embeddings",
                status="started",
                input_data={"batch_size": batch_size}
            )
            
            # Perform batch update
            updated_count = await self.embedding_service.batch_update_embeddings(batch_size)
            
            # Log success
            await self.log_activity(
                action="batch_update_embeddings",
                status="completed",
                output_data={"updated_count": updated_count}
            )
            
            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"Updated {updated_count} embeddings"
            }
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            await self.log_activity(
                action="batch_update_embeddings",
                status="failed",
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings in the system
        
        Returns:
            Embedding statistics
        """
        try:
            # Log stats request
            await self.log_activity(
                action="get_embedding_stats",
                status="started"
            )
            
            # Get stats
            stats = await self.embedding_service.get_embedding_stats()
            
            # Log success
            await self.log_activity(
                action="get_embedding_stats",
                status="completed",
                output_data=stats
            )
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            await self.log_activity(
                action="get_embedding_stats",
                status="failed",
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the semantic agent
        
        Returns:
            Health check results
        """
        try:
            # Check if embedding service is working
            test_embedding = await self.embedding_service.generate_embedding("test content")
            
            # Get current stats
            stats = await self.embedding_service.get_embedding_stats()
            
            return {
                "status": "healthy",
                "embedding_service": "operational",
                "model": self.embedding_service.model_name,
                "stats": stats,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming messages for the semantic agent
        
        Args:
            message: Message to process
            
        Returns:
            Processing result
        """
        try:
            action = message.get("action")
            
            if action == "process_idea":
                idea_id = message.get("idea_id")
                if not idea_id:
                    return {"success": False, "error": "idea_id required"}
                return await self.process_idea(idea_id)
            
            elif action == "search_similar":
                query = message.get("query")
                user_id = message.get("user_id")
                if not query or not user_id:
                    return {"success": False, "error": "query and user_id required"}
                return await self.search_similar_ideas(query, user_id, **message)
            
            elif action == "find_related":
                idea_id = message.get("idea_id")
                if not idea_id:
                    return {"success": False, "error": "idea_id required"}
                return await self.find_related_ideas(idea_id, **message)
            
            elif action == "batch_update":
                batch_size = message.get("batch_size", 50)
                return await self.batch_update_embeddings(batch_size)
            
            elif action == "get_stats":
                return await self.get_embedding_stats()
            
            elif action == "health_check":
                return await self.health_check()
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"success": False, "error": str(e)}

# Global instance
semantic_agent = SemanticAgent()