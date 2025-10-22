"""
Background Tasks for Embedding Generation
Handles automatic embedding generation for new ideas
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

try:  # pragma: no cover
    from ..database.database import SessionLocal
    from ..database.models import Idea, Agent, AgentLog
    from ..services.embedding_service import embedding_service
    from ..agents.agent_semantic import semantic_agent
except ImportError:  # pragma: no cover
    from database.database import SessionLocal
    from database.models import Idea, Agent, AgentLog
    from services.embedding_service import embedding_service
    from agents.agent_semantic import semantic_agent

logger = logging.getLogger(__name__)

class EmbeddingTaskManager:
    """Manages background tasks for embedding generation"""
    
    def __init__(self):
        self.is_running = False
        self.task_interval = 300  # 5 minutes
        self.batch_size = 10
        self.max_retries = 3
    
    async def start(self):
        """Start the embedding task manager"""
        if self.is_running:
            logger.warning("Embedding task manager is already running")
            return
        
        self.is_running = True
        logger.info("Starting embedding task manager")
        
        try:
            while self.is_running:
                await self.process_pending_embeddings()
                await asyncio.sleep(self.task_interval)
        except Exception as e:
            logger.error(f"Embedding task manager error: {e}")
        finally:
            self.is_running = False
            logger.info("Embedding task manager stopped")
    
    async def stop(self):
        """Stop the embedding task manager"""
        logger.info("Stopping embedding task manager")
        self.is_running = False
    
    async def process_pending_embeddings(self):
        """Process ideas that need embeddings"""
        try:
            # Get ideas without embeddings
            pending_ideas = await self.get_pending_ideas()
            
            if not pending_ideas:
                logger.debug("No pending ideas for embedding generation")
                return
            
            logger.info(f"Processing {len(pending_ideas)} ideas for embedding generation")
            
            # Process ideas in batches
            for i in range(0, len(pending_ideas), self.batch_size):
                batch = pending_ideas[i:i + self.batch_size]
                await self.process_batch(batch)
                
                # Small delay between batches
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing pending embeddings: {e}")
    
    async def get_pending_ideas(self) -> List[Dict[str, Any]]:
        """Get ideas that need embeddings"""
        try:
            db = SessionLocal()
            try:
                # Get ideas without embeddings or with outdated embeddings
                ideas = db.query(Idea).filter(
                    and_(
                        Idea.is_archived == False,
                        Idea.processing_status == 'completed',
                        or_(
                            Idea.content_embedding.is_(None),
                            and_(
                                Idea.embedding_updated_at.is_(None),
                                Idea.updated_at > Idea.embedding_updated_at
                            )
                        )
                    )
                ).order_by(Idea.created_at.desc()).limit(50).all()
                
                return [
                    {
                        'id': idea.id,
                        'content': idea.content_processed or idea.content_transcribed or idea.content_raw,
                        'user_id': idea.user_id,
                        'category': idea.category,
                        'created_at': idea.created_at,
                        'updated_at': idea.updated_at
                    }
                    for idea in ideas
                    if idea.content_processed or idea.content_transcribed or idea.content_raw
                ]
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get pending ideas: {e}")
            return []
    
    async def process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of ideas for embedding generation"""
        try:
            for idea_data in batch:
                try:
                    # Generate embedding for the idea
                    result = await semantic_agent.process_idea(idea_data['id'])
                    
                    if result.get('success'):
                        logger.info(f"Generated embedding for idea {idea_data['id']}")
                    else:
                        logger.warning(f"Failed to generate embedding for idea {idea_data['id']}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error processing idea {idea_data['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
    
    async def cleanup_old_embeddings(self):
        """Clean up old embeddings that are no longer needed"""
        try:
            db = SessionLocal()
            try:
                # Find ideas with outdated embeddings (older than 30 days and content updated)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                outdated_ideas = db.query(Idea).filter(
                    and_(
                        Idea.embedding_updated_at < cutoff_date,
                        Idea.updated_at > Idea.embedding_updated_at,
                        Idea.content_embedding.isnot(None)
                    )
                ).all()
                
                if outdated_ideas:
                    logger.info(f"Found {len(outdated_ideas)} ideas with outdated embeddings")
                    
                    # Clear outdated embeddings
                    for idea in outdated_ideas:
                        idea.content_embedding = None
                        idea.embedding_model = None
                        idea.embedding_updated_at = None
                    
                    db.commit()
                    logger.info(f"Cleared {len(outdated_ideas)} outdated embeddings")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error cleaning up old embeddings: {e}")
    
    async def get_embedding_health(self) -> Dict[str, Any]:
        """Get health status of embedding system"""
        try:
            db = SessionLocal()
            try:
                # Get basic stats
                total_ideas = db.query(Idea).filter(Idea.is_archived == False).count()
                ideas_with_embeddings = db.query(Idea).filter(
                    and_(
                        Idea.is_archived == False,
                        Idea.content_embedding.isnot(None)
                    )
                ).count()
                
                pending_ideas = db.query(Idea).filter(
                    and_(
                        Idea.is_archived == False,
                        Idea.processing_status == 'completed',
                        Idea.content_embedding.is_(None)
                    )
                ).count()
                
                # Get recent activity
                recent_updates = db.query(AgentLog).filter(
                    and_(
                        AgentLog.agent_id == 'semantic',
                        AgentLog.action == 'generate_embedding',
                        AgentLog.started_at > datetime.utcnow() - timedelta(hours=24)
                    )
                ).count()
                
                coverage = (ideas_with_embeddings / total_ideas * 100) if total_ideas > 0 else 0
                
                return {
                    'status': 'healthy' if coverage > 80 else 'degraded' if coverage > 50 else 'unhealthy',
                    'total_ideas': total_ideas,
                    'ideas_with_embeddings': ideas_with_embeddings,
                    'pending_ideas': pending_ideas,
                    'coverage_percentage': coverage,
                    'recent_updates_24h': recent_updates,
                    'task_manager_running': self.is_running,
                    'last_check': datetime.utcnow().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting embedding health: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }

# Global task manager instance
embedding_task_manager = EmbeddingTaskManager()

async def start_embedding_tasks():
    """Start background embedding tasks"""
    await embedding_task_manager.start()

async def stop_embedding_tasks():
    """Stop background embedding tasks"""
    await embedding_task_manager.stop()

async def trigger_embedding_generation():
    """Manually trigger embedding generation"""
    await embedding_task_manager.process_pending_embeddings()

async def get_embedding_health():
    """Get embedding system health"""
    return await embedding_task_manager.get_embedding_health()