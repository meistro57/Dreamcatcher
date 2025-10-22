from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from datetime import datetime, timedelta
import json

from .models import (
    Idea, Tag, IdeaExpansion, IdeaVisual, Proposal, ProposalTask,
    Agent, AgentLog, SystemMetrics, ScheduledTask
)

TModel = TypeVar("TModel")


class BaseCRUD(Generic[TModel]):
    """Reusable CRUD helper that wraps common persistence operations."""

    def __init__(self, db: Session, model: Type[TModel]):
        self.db = db
        self.model = model

    def get(self, **filters) -> Optional[TModel]:
        """Return the first record matching the provided filters."""
        return self.db.query(self.model).filter_by(**filters).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[TModel]:
        """Return a paginated list of model instances."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, **data) -> TModel:
        """Create and persist a new model instance."""
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, instance: TModel, **data) -> TModel:
        """Apply updates to an instance and persist the changes."""
        for key, value in data.items():
            setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: TModel) -> None:
        """Remove an instance from the database."""
        self.db.delete(instance)
        self.db.commit()


class IdeaCRUD:
    """CRUD operations for Ideas"""
    
    @staticmethod
    def create_idea(db: Session, content: str, source_type: str, **kwargs) -> Idea:
        """Create a new idea"""
        idea = Idea(
            content_raw=content,
            source_type=source_type,
            **kwargs
        )
        db.add(idea)
        db.commit()
        db.refresh(idea)
        return idea
    
    @staticmethod
    def get_idea(db: Session, idea_id: str) -> Optional[Idea]:
        """Get idea by ID"""
        return db.query(Idea).filter(Idea.id == idea_id).first()
    
    @staticmethod
    def get_ideas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        min_urgency: Optional[float] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Idea]:
        """Get ideas with filtering"""
        query = db.query(Idea)
        
        if category:
            query = query.filter(Idea.category == category)
        
        if source_type:
            query = query.filter(Idea.source_type == source_type)
        
        if min_urgency is not None:
            query = query.filter(Idea.urgency_score >= min_urgency)
        
        if tags:
            query = query.join(Idea.tags).filter(Tag.name.in_(tags))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Idea.content_raw.ilike(search_term),
                    Idea.content_transcribed.ilike(search_term),
                    Idea.content_processed.ilike(search_term)
                )
            )
        
        return query.order_by(desc(Idea.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_idea(db: Session, idea_id: str, **kwargs) -> Optional[Idea]:
        """Update an idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            for key, value in kwargs.items():
                setattr(idea, key, value)
            idea.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(idea)
        return idea
    
    @staticmethod
    def delete_idea(db: Session, idea_id: str) -> bool:
        """Delete an idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            db.delete(idea)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_related_ideas(db: Session, idea_id: str) -> List[Idea]:
        """Get ideas related to a specific idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            return idea.related_ideas
        return []
    
    @staticmethod
    def get_ideas_by_urgency(db: Session, min_score: float = 80.0) -> List[Idea]:
        """Get high-urgency ideas"""
        return db.query(Idea).filter(
            and_(
                Idea.urgency_score >= min_score,
                Idea.is_archived == False
            )
        ).order_by(desc(Idea.urgency_score)).all()
    
    @staticmethod
    def get_stale_ideas(db: Session, days: int = 7) -> List[Idea]:
        """Get ideas that haven't been updated recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Idea).filter(
            and_(
                Idea.updated_at < cutoff_date,
                Idea.is_archived == False,
                Idea.urgency_score > 50.0
            )
        ).all()
    
    @staticmethod
    def get_dormant_ideas(db: Session, days: int = 30) -> List[Idea]:
        """Get dormant ideas that haven't been processed recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Idea).filter(
            and_(
                Idea.updated_at < cutoff_date,
                Idea.is_archived == False,
                Idea.urgency_score < 30.0
            )
        ).order_by(desc(Idea.created_at)).all()
    
    @staticmethod
    def get_ideas_for_context_review(db: Session, limit: int = 50) -> List[Idea]:
        """Get ideas that need context review"""
        return db.query(Idea).filter(
            and_(
                Idea.is_archived == False,
                or_(
                    Idea.content_processed.is_(None),
                    Idea.content_processed == ''
                )
            )
        ).order_by(desc(Idea.urgency_score)).limit(limit).all()
    
    @staticmethod
    def get_ideas_by_patterns(db: Session, patterns: List[str]) -> List[Idea]:
        """Get ideas matching specific patterns"""
        if not patterns:
            return []
        
        pattern_conditions = []
        for pattern in patterns:
            pattern_term = f"%{pattern}%"
            pattern_conditions.append(
                or_(
                    Idea.content_raw.ilike(pattern_term),
                    Idea.content_transcribed.ilike(pattern_term),
                    Idea.content_processed.ilike(pattern_term)
                )
            )
        
        return db.query(Idea).filter(
            and_(
                Idea.is_archived == False,
                or_(*pattern_conditions)
            )
        ).order_by(desc(Idea.urgency_score)).all()
    
    @staticmethod
    def get_random_ideas(db: Session, count: int = 10) -> List[Idea]:
        """Get random ideas for serendipity reviews"""
        from sqlalchemy.sql import func
        return db.query(Idea).filter(
            Idea.is_archived == False
        ).order_by(func.random()).limit(count).all()
    
    @staticmethod
    def get_successful_ideas(db: Session, min_score: float = 70.0) -> List[Idea]:
        """Get successful ideas for pattern analysis"""
        return db.query(Idea).filter(
            and_(
                Idea.is_archived == False,
                Idea.urgency_score >= min_score,
                Idea.quality_score >= min_score
            )
        ).order_by(desc(Idea.quality_score)).all()
    
    @staticmethod
    def update_idea_urgency(db: Session, idea_id: str, urgency_score: float) -> Optional[Idea]:
        """Update idea urgency score"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            idea.urgency_score = urgency_score
            idea.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(idea)
        return idea
    
    @staticmethod
    def archive_idea(db: Session, idea_id: str, reason: str = '') -> Optional[Idea]:
        """Archive an idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            idea.is_archived = True
            idea.archived_reason = reason
            idea.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(idea)
        return idea

class TagCRUD:
    """CRUD operations for Tags"""
    
    @staticmethod
    def create_tag(db: Session, name: str, color: str = '#3B82F6', description: str = '') -> Tag:
        """Create a new tag"""
        tag = Tag(name=name, color=color, description=description)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def get_or_create_tag(db: Session, name: str) -> Tag:
        """Get existing tag or create new one"""
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = TagCRUD.create_tag(db, name)
        return tag
    
    @staticmethod
    def get_all_tags(db: Session) -> List[Tag]:
        """Get all tags"""
        return db.query(Tag).all()

class ExpansionCRUD:
    """CRUD operations for Idea Expansions"""
    
    @staticmethod
    def create_expansion(
        db: Session, 
        idea_id: str, 
        content: str, 
        expansion_type: str,
        prompt_used: str = '',
        agent_version: str = '1.0.0'
    ) -> IdeaExpansion:
        """Create a new idea expansion"""
        expansion = IdeaExpansion(
            idea_id=idea_id,
            expanded_content=content,
            expansion_type=expansion_type,
            prompt_used=prompt_used,
            agent_version=agent_version
        )
        db.add(expansion)
        db.commit()
        db.refresh(expansion)
        return expansion
    
    @staticmethod
    def get_expansions_for_idea(db: Session, idea_id: str) -> List[IdeaExpansion]:
        """Get all expansions for an idea"""
        return db.query(IdeaExpansion).filter(IdeaExpansion.idea_id == idea_id).all()

class VisualCRUD:
    """CRUD operations for Idea Visuals"""
    
    @staticmethod
    def create_visual(
        db: Session,
        idea_id: str,
        image_path: str,
        prompt_used: str = '',
        style_config: Optional[Dict] = None,
        generation_params: Optional[Dict] = None
    ) -> IdeaVisual:
        """Create a new idea visual"""
        visual = IdeaVisual(
            idea_id=idea_id,
            image_path=image_path,
            prompt_used=prompt_used,
            style_config=style_config or {},
            generation_params=generation_params or {}
        )
        db.add(visual)
        db.commit()
        db.refresh(visual)
        return visual
    
    @staticmethod
    def get_visuals_for_idea(db: Session, idea_id: str) -> List[IdeaVisual]:
        """Get all visuals for an idea"""
        return db.query(IdeaVisual).filter(IdeaVisual.idea_id == idea_id).all()
    
    @staticmethod
    def approve_visual(db: Session, visual_id: str, quality_score: float = 85.0) -> Optional[IdeaVisual]:
        """Approve a visual"""
        visual = db.query(IdeaVisual).filter(IdeaVisual.id == visual_id).first()
        if visual:
            visual.is_approved = True
            visual.quality_score = quality_score
            db.commit()
            db.refresh(visual)
        return visual

class ProposalCRUD:
    """CRUD operations for Proposals"""
    
    @staticmethod
    def create_proposal(
        db: Session,
        idea_id: str,
        title: str,
        description: str,
        problem_statement: str = '',
        solution_approach: str = '',
        implementation_plan: Optional[Dict] = None,
        generated_by: str = 'system'
    ) -> Proposal:
        """Create a new proposal"""
        proposal = Proposal(
            idea_id=idea_id,
            title=title,
            description=description,
            problem_statement=problem_statement,
            solution_approach=solution_approach,
            implementation_plan=implementation_plan or {},
            generated_by=generated_by
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return proposal
    
    @staticmethod
    def get_pending_proposals(db: Session) -> List[Proposal]:
        """Get all pending proposals"""
        return db.query(Proposal).filter(Proposal.status == 'pending').all()
    
    @staticmethod
    def approve_proposal(db: Session, proposal_id: str, notes: str = '') -> Optional[Proposal]:
        """Approve a proposal"""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal:
            proposal.status = 'approved'
            proposal.approval_notes = notes
            proposal.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(proposal)
        return proposal

class AgentCRUD:
    """CRUD operations for Agents"""
    
    @staticmethod
    def create_or_update_agent(
        db: Session,
        agent_id: str,
        name: str,
        description: str = '',
        version: str = '1.0.0',
        config: Optional[Dict] = None
    ) -> Agent:
        """Create or update an agent"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            agent = Agent(
                id=agent_id,
                name=name,
                description=description,
                version=version,
                config=config or {}
            )
            db.add(agent)
        else:
            agent.name = name
            agent.description = description
            agent.version = version
            agent.config = config or {}
            agent.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agent)
        return agent
    
    @staticmethod
    def log_agent_activity(
        db: Session,
        agent_id: str,
        action: str,
        status: str,
        idea_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> AgentLog:
        """Log agent activity"""
        log = AgentLog(
            agent_id=agent_id,
            idea_id=idea_id,
            action=action,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            started_at=started_at or datetime.utcnow(),
            completed_at=completed_at
        )
        
        if started_at and completed_at:
            log.processing_time = (completed_at - started_at).total_seconds()
        
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_agent_performance(db: Session, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get agent performance metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logs = db.query(AgentLog).filter(
            and_(
                AgentLog.agent_id == agent_id,
                AgentLog.started_at >= cutoff_date
            )
        ).all()
        
        total_tasks = len(logs)
        successful_tasks = len([log for log in logs if log.status == 'completed'])
        failed_tasks = len([log for log in logs if log.status == 'failed'])
        
        avg_processing_time = 0
        if logs:
            processing_times = [log.processing_time for log in logs if log.processing_time]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': (successful_tasks / total_tasks) if total_tasks > 0 else 0,
            'avg_processing_time': avg_processing_time
        }
    
    @staticmethod
    def get_all_agents(db: Session) -> List[Agent]:
        """Get all registered agents"""
        return db.query(Agent).all()
    
    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return db.query(Agent).filter(Agent.id == agent_id).first()

class SystemMetricsCRUD:
    """CRUD operations for System Metrics"""
    
    @staticmethod
    def record_metric(
        db: Session,
        metric_name: str,
        metric_value: float,
        metric_type: str = 'gauge',
        metadata: Optional[Dict] = None
    ) -> SystemMetrics:
        """Record a system metric"""
        metric = SystemMetrics(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            metadata=metadata or {}
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric
    
    @staticmethod
    def get_metrics(
        db: Session,
        metric_name: Optional[str] = None,
        hours: int = 24
    ) -> List[SystemMetrics]:
        """Get system metrics"""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(SystemMetrics).filter(
            SystemMetrics.timestamp >= cutoff_date
        )
        
        if metric_name:
            query = query.filter(SystemMetrics.metric_name == metric_name)
        
        return query.order_by(desc(SystemMetrics.timestamp)).all()
    
    @staticmethod
    def get_latest_metrics(db: Session) -> List[SystemMetrics]:
        """Get latest values for all metrics"""
        from sqlalchemy.sql import func
        
        subquery = db.query(
            SystemMetrics.metric_name,
            func.max(SystemMetrics.timestamp).label('latest_timestamp')
        ).group_by(SystemMetrics.metric_name).subquery()
        
        return db.query(SystemMetrics).join(
            subquery,
            and_(
                SystemMetrics.metric_name == subquery.c.metric_name,
                SystemMetrics.timestamp == subquery.c.latest_timestamp
            )
        ).all()

class AgentLogCRUD:
    """CRUD operations for Agent Logs"""
    
    @staticmethod
    def get_agent_logs(
        db: Session,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        hours: int = 24
    ) -> List[AgentLog]:
        """Get agent logs with filtering"""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(AgentLog).filter(
            AgentLog.started_at >= cutoff_date
        )
        
        if agent_id:
            query = query.filter(AgentLog.agent_id == agent_id)
        
        if status:
            query = query.filter(AgentLog.status == status)
        
        return query.order_by(desc(AgentLog.started_at)).all()
    
    @staticmethod
    def get_error_logs(db: Session, hours: int = 24) -> List[AgentLog]:
        """Get error logs"""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        return db.query(AgentLog).filter(
            and_(
                AgentLog.status == 'failed',
                AgentLog.started_at >= cutoff_date,
                AgentLog.error_message.is_not(None)
            )
        ).order_by(desc(AgentLog.started_at)).all()
    
    @staticmethod
    def get_performance_summary(db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary across all agents"""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        
        logs = db.query(AgentLog).filter(
            AgentLog.started_at >= cutoff_date
        ).all()
        
        total_tasks = len(logs)
        successful_tasks = len([log for log in logs if log.status == 'completed'])
        failed_tasks = len([log for log in logs if log.status == 'failed'])
        in_progress_tasks = len([log for log in logs if log.status == 'started'])
        
        agent_stats = {}
        for log in logs:
            if log.agent_id not in agent_stats:
                agent_stats[log.agent_id] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'in_progress': 0
                }
            agent_stats[log.agent_id]['total'] += 1
            if log.status == 'completed':
                agent_stats[log.agent_id]['successful'] += 1
            elif log.status == 'failed':
                agent_stats[log.agent_id]['failed'] += 1
            elif log.status == 'started':
                agent_stats[log.agent_id]['in_progress'] += 1
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'success_rate': (successful_tasks / total_tasks) if total_tasks > 0 else 0,
            'agent_stats': agent_stats
        }

class VisualizationCRUD:
    """CRUD operations for Visualizations"""
    
    @staticmethod
    def create_visualization(
        db: Session,
        idea_id: str,
        visualization_type: str,
        data: Dict[str, Any],
        config: Optional[Dict] = None
    ) -> IdeaVisual:
        """Create a visualization record"""
        visual = IdeaVisual(
            idea_id=idea_id,
            image_path=f"viz_{idea_id}_{visualization_type}.json",
            prompt_used=f"Generated {visualization_type} visualization",
            style_config=config or {},
            generation_params={'type': visualization_type, 'data': data}
        )
        db.add(visual)
        db.commit()
        db.refresh(visual)
        return visual
    
    @staticmethod
    def get_visualizations(
        db: Session,
        idea_id: Optional[str] = None,
        viz_type: Optional[str] = None
    ) -> List[IdeaVisual]:
        """Get visualizations with filtering"""
        query = db.query(IdeaVisual)
        
        if idea_id:
            query = query.filter(IdeaVisual.idea_id == idea_id)
        
        if viz_type:
            query = query.filter(
                IdeaVisual.generation_params['type'].astext == viz_type
            )
        
        return query.order_by(desc(IdeaVisual.created_at)).all()
    
    @staticmethod
    def update_visualization_quality(
        db: Session,
        visual_id: str,
        quality_score: float,
        feedback: str = ''
    ) -> Optional[IdeaVisual]:
        """Update visualization quality score"""
        visual = db.query(IdeaVisual).filter(IdeaVisual.id == visual_id).first()
        if visual:
            visual.quality_score = quality_score
            visual.style_config['feedback'] = feedback
            visual.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(visual)
        return visual

class TaskCRUD:
    """CRUD operations for Scheduled Tasks"""
    
    @staticmethod
    def create_task(
        db: Session,
        task_type: str,
        target_agent: str,
        task_data: Dict[str, Any],
        schedule_time: Optional[datetime] = None
    ) -> ScheduledTask:
        """Create a scheduled task"""
        task = ScheduledTask(
            task_type=task_type,
            target_agent=target_agent,
            task_data=task_data,
            schedule_time=schedule_time or datetime.utcnow()
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_pending_tasks(db: Session) -> List[ScheduledTask]:
        """Get pending tasks"""
        return db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.status == 'pending',
                ScheduledTask.schedule_time <= datetime.utcnow()
            )
        ).order_by(ScheduledTask.schedule_time).all()
    
    @staticmethod
    def complete_task(db: Session, task_id: str, result: Optional[Dict] = None) -> Optional[ScheduledTask]:
        """Mark task as completed"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            task.status = 'completed'
            task.result = result or {}
            task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def fail_task(db: Session, task_id: str, error_message: str) -> Optional[ScheduledTask]:
        """Mark task as failed"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            task.status = 'failed'
            task.error_message = error_message
            task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task