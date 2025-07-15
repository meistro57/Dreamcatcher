import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database import get_db, IdeaCRUD, AgentCRUD
from agents import agent_registry, AgentListener, AgentClassifier
from services import AIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dreamcatcher.scheduler")

class DreamcatcherScheduler:
    """
    Scheduler for periodic tasks in the Dreamcatcher system
    Handles idea review, agent maintenance, and system optimization
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_service = AIService()
        self.shutdown_event = asyncio.Event()
        
        # Initialize agents
        self.listener_agent = AgentListener()
        self.classifier_agent = AgentClassifier()
        
        # Register agents
        agent_registry.register(self.listener_agent)
        agent_registry.register(self.classifier_agent)
    
    async def start(self):
        """Start the scheduler"""
        logger.info("Starting Dreamcatcher scheduler...")
        
        # Schedule periodic tasks
        self._schedule_tasks()
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Keep running until shutdown
        await self.shutdown_event.wait()
    
    def _schedule_tasks(self):
        """Schedule all periodic tasks"""
        
        # Review stale ideas every hour
        self.scheduler.add_job(
            self.review_stale_ideas,
            trigger=IntervalTrigger(hours=1),
            id='review_stale_ideas',
            name='Review stale ideas',
            max_instances=1
        )
        
        # Review high-priority ideas every 30 minutes
        self.scheduler.add_job(
            self.review_high_priority_ideas,
            trigger=IntervalTrigger(minutes=30),
            id='review_high_priority',
            name='Review high-priority ideas',
            max_instances=1
        )
        
        # Weekly idea pattern analysis
        self.scheduler.add_job(
            self.analyze_idea_patterns,
            trigger=CronTrigger(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
            id='analyze_patterns',
            name='Analyze idea patterns',
            max_instances=1
        )
        
        # Daily system health check
        self.scheduler.add_job(
            self.system_health_check,
            trigger=CronTrigger(hour=2, minute=0),  # Daily at 2 AM
            id='health_check',
            name='System health check',
            max_instances=1
        )
        
        # Agent performance review every 6 hours
        self.scheduler.add_job(
            self.review_agent_performance,
            trigger=IntervalTrigger(hours=6),
            id='agent_performance',
            name='Review agent performance',
            max_instances=1
        )
        
        # Cleanup old data weekly
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=CronTrigger(hour=4, minute=0, day_of_week=0),  # Sunday 4 AM
            id='cleanup_data',
            name='Cleanup old data',
            max_instances=1
        )
    
    async def review_stale_ideas(self):
        """Review ideas that haven't been updated recently"""
        logger.info("Starting stale idea review...")
        
        try:
            with get_db() as db:
                # Get ideas older than 7 days with high scores
                stale_ideas = IdeaCRUD.get_stale_ideas(db, days=7)
                
                logger.info(f"Found {len(stale_ideas)} stale ideas for review")
                
                for idea in stale_ideas:
                    # Re-evaluate the idea
                    if self.ai_service.is_available():
                        try:
                            content = idea.content_transcribed or idea.content_raw
                            analysis = await self.ai_service.analyze_idea(content)
                            
                            # Update idea based on analysis
                            if analysis:
                                IdeaCRUD.update_idea(
                                    db=db,
                                    idea_id=idea.id,
                                    viability_score=analysis.get('viability_score', idea.viability_score),
                                    novelty_score=analysis.get('novelty_score', idea.novelty_score)
                                )
                                
                                logger.info(f"Updated stale idea {idea.id}")
                        
                        except Exception as e:
                            logger.error(f"Failed to re-analyze idea {idea.id}: {e}")
                
                logger.info("Stale idea review completed")
                
        except Exception as e:
            logger.error(f"Stale idea review failed: {e}")
    
    async def review_high_priority_ideas(self):
        """Review high-priority ideas for potential action"""
        logger.info("Starting high-priority idea review...")
        
        try:
            with get_db() as db:
                # Get high-urgency ideas
                high_priority_ideas = IdeaCRUD.get_ideas_by_urgency(db, min_score=80.0)
                
                logger.info(f"Found {len(high_priority_ideas)} high-priority ideas")
                
                for idea in high_priority_ideas:
                    # Check if idea has been acted upon recently
                    if not idea.proposals or not any(p.status == 'approved' for p in idea.proposals):
                        # Generate a proposal if none exists or none are approved
                        if self.ai_service.is_available():
                            try:
                                content = idea.content_transcribed or idea.content_raw
                                classification = {
                                    'category': idea.category,
                                    'urgency_score': idea.urgency_score,
                                    'novelty_score': idea.novelty_score
                                }
                                
                                proposal_data = await self.ai_service.generate_proposal(
                                    content, classification
                                )
                                
                                if proposal_data:
                                    # Create proposal in database
                                    from database import ProposalCRUD
                                    ProposalCRUD.create_proposal(
                                        db=db,
                                        idea_id=idea.id,
                                        title=proposal_data.get('title', f'Proposal for {idea.id}'),
                                        description=proposal_data.get('solution_approach', ''),
                                        problem_statement=proposal_data.get('problem_statement', ''),
                                        implementation_plan=proposal_data.get('implementation_plan', {}),
                                        generated_by='scheduler'
                                    )
                                    
                                    logger.info(f"Generated proposal for high-priority idea {idea.id}")
                            
                            except Exception as e:
                                logger.error(f"Failed to generate proposal for idea {idea.id}: {e}")
                
                logger.info("High-priority idea review completed")
                
        except Exception as e:
            logger.error(f"High-priority idea review failed: {e}")
    
    async def analyze_idea_patterns(self):
        """Analyze patterns in captured ideas"""
        logger.info("Starting weekly idea pattern analysis...")
        
        try:
            with get_db() as db:
                # Get ideas from the last week
                week_ago = datetime.utcnow() - timedelta(days=7)
                ideas = db.query(Idea).filter(Idea.created_at >= week_ago).all()
                
                logger.info(f"Analyzing {len(ideas)} ideas from the past week")
                
                # Basic pattern analysis
                patterns = {
                    'total_ideas': len(ideas),
                    'by_source': {},
                    'by_category': {},
                    'high_urgency_count': 0,
                    'avg_urgency': 0,
                    'peak_hours': {}
                }
                
                urgency_scores = []
                
                for idea in ideas:
                    # Source type distribution
                    source = idea.source_type
                    patterns['by_source'][source] = patterns['by_source'].get(source, 0) + 1
                    
                    # Category distribution
                    category = idea.category or 'uncategorized'
                    patterns['by_category'][category] = patterns['by_category'].get(category, 0) + 1
                    
                    # Urgency analysis
                    if idea.urgency_score:
                        urgency_scores.append(idea.urgency_score)
                        if idea.urgency_score > 80:
                            patterns['high_urgency_count'] += 1
                    
                    # Peak hours analysis
                    hour = idea.created_at.hour
                    patterns['peak_hours'][hour] = patterns['peak_hours'].get(hour, 0) + 1
                
                if urgency_scores:
                    patterns['avg_urgency'] = sum(urgency_scores) / len(urgency_scores)
                
                # Log findings
                logger.info(f"Pattern analysis results: {patterns}")
                
                # If AI is available, get deeper insights
                if self.ai_service.is_available():
                    try:
                        # Analyze content themes
                        content_sample = [
                            idea.content_transcribed or idea.content_raw 
                            for idea in ideas[:10]  # Sample of 10 ideas
                        ]
                        
                        analysis_prompt = f"""
                        Analyze these recent ideas for patterns and themes:
                        
                        {chr(10).join(content_sample)}
                        
                        Provide insights about:
                        1. Common themes
                        2. Creative patterns
                        3. Areas of focus
                        4. Recommendations for the user
                        
                        Keep it concise and actionable.
                        """
                        
                        insights = await self.ai_service.get_completion(analysis_prompt)
                        
                        if insights:
                            logger.info(f"AI insights: {insights}")
                    
                    except Exception as e:
                        logger.error(f"AI pattern analysis failed: {e}")
                
                logger.info("Weekly idea pattern analysis completed")
                
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
    
    async def system_health_check(self):
        """Perform system health check"""
        logger.info("Starting system health check...")
        
        try:
            health_report = {
                'timestamp': datetime.utcnow().isoformat(),
                'database': False,
                'ai_service': False,
                'agents': {},
                'storage': False
            }
            
            # Check database connectivity
            try:
                with get_db() as db:
                    db.execute("SELECT 1")
                    health_report['database'] = True
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
            
            # Check AI service
            health_report['ai_service'] = self.ai_service.is_available()
            
            # Check agents
            for agent in agent_registry.get_all_agents():
                health_report['agents'][agent.agent_id] = {
                    'active': agent.is_active,
                    'processed': agent.total_processed,
                    'success_rate': agent.success_count / agent.total_processed if agent.total_processed > 0 else 0
                }
            
            # Check storage
            try:
                storage_path = os.path.join(os.getcwd(), 'storage')
                if os.path.exists(storage_path):
                    health_report['storage'] = True
            except Exception as e:
                logger.error(f"Storage health check failed: {e}")
            
            logger.info(f"Health check completed: {health_report}")
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
    
    async def review_agent_performance(self):
        """Review and optimize agent performance"""
        logger.info("Starting agent performance review...")
        
        try:
            with get_db() as db:
                for agent in agent_registry.get_all_agents():
                    performance = AgentCRUD.get_agent_performance(db, agent.agent_id)
                    
                    logger.info(f"Agent {agent.agent_id} performance: {performance}")
                    
                    # If performance is poor, could trigger optimization
                    if performance.get('success_rate', 0) < 0.8:  # Less than 80% success rate
                        logger.warning(f"Agent {agent.agent_id} has low success rate: {performance.get('success_rate', 0)}")
                        
                        # Could trigger agent optimization here
                        # For now, just log
                
                logger.info("Agent performance review completed")
                
        except Exception as e:
            logger.error(f"Agent performance review failed: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old data to keep database size manageable"""
        logger.info("Starting data cleanup...")
        
        try:
            with get_db() as db:
                # Clean up old agent logs (older than 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                old_logs = db.query(AgentLog).filter(AgentLog.started_at < thirty_days_ago).all()
                
                if old_logs:
                    for log in old_logs:
                        db.delete(log)
                    db.commit()
                    logger.info(f"Cleaned up {len(old_logs)} old agent logs")
                
                # Clean up old system metrics (older than 90 days)
                ninety_days_ago = datetime.utcnow() - timedelta(days=90)
                
                old_metrics = db.query(SystemMetrics).filter(SystemMetrics.timestamp < ninety_days_ago).all()
                
                if old_metrics:
                    for metric in old_metrics:
                        db.delete(metric)
                    db.commit()
                    logger.info(f"Cleaned up {len(old_metrics)} old system metrics")
                
                logger.info("Data cleanup completed")
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown()
        self.shutdown_event.set()

# Global scheduler instance
scheduler = DreamcatcherScheduler()

async def main():
    """Main function"""
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        scheduler.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        scheduler.shutdown()
        raise

if __name__ == "__main__":
    asyncio.run(main())